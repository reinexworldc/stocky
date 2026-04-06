"""Agentic chat orchestrator.

When LLM is available the agent runs an autonomous tool-calling loop:
  1. Build system prompt with available tools
  2. Send conversation history + user message to LLM with function definitions
  3. If LLM returns tool_calls, execute them and feed results back
  4. Repeat until LLM returns a final text response (max N iterations)

When LLM is NOT available the agent falls back to rule-based routing
that picks tools based on keywords and builds a deterministic reply.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from difflib import get_close_matches
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.llm import get_llm_provider
from app.llm.base import LLMMessage, LLMToolCallRequest
from app.models import Product
from app.services.analyze_full_catalog import analyze_full_catalog
from app.services.build_purchase_order import build_purchase_order
from app.services.conversation_memory import (
    ConversationEntry,
    store as conversation_store,
)
from app.services.explain_decision import explain_decision_for_sku
from app.services.flag_dead_stock import flag_dead_stock
from app.services.forecast_demand import forecast_demand
from app.services.get_item_deep_dive import get_item_deep_dive

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 6
MAX_PARALLEL_TOOL_CALLS = 4

# ---------------------------------------------------------------------------
# Tool definitions (OpenAI function-calling schema)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "analyze_full_catalog",
            "description": (
                "Analyzes the entire product catalog. Shows a summary of critical, "
                "warning, and stable SKUs, a traffic light indicator, and top problem items. "
                "Call this when the user asks for a general warehouse overview, what's happening, "
                "or which items are at risk."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_item_deep_dive",
            "description": (
                "Deep analysis of a single SKU: stock levels, sales velocity, trend, demand "
                "forecast, purchase recommendation, and text explanation. "
                "Call this when the user asks about a specific product or SKU."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Product SKU, e.g. LAP-15 or CHAIR-07",
                    }
                },
                "required": ["sku"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_demand",
            "description": (
                "Demand forecast for a single SKU over 7, 14, and 30 day horizons. "
                "Uses blended velocity from 7-day and 30-day sales data. "
                "Call this when the user asks about the forecast, demand, or trend "
                "of a specific product."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Product SKU",
                    }
                },
                "required": ["sku"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_purchase_order",
            "description": (
                "Generates a purchase order draft: groups critical and warning items "
                "by supplier, calculates quantities and totals. You can pass supplier_id "
                "to filter by a single supplier. "
                "Call this when the user asks what to order, purchase plan, "
                "or supplier order."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_id": {
                        "type": "string",
                        "description": "Supplier UUID for filtering (optional)",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_dead_stock",
            "description": (
                "Finds dead stock items: products with no sales or very low movement. "
                "Shows severity, frozen value, and recommended action. "
                "Call this when the user asks about dead stock, stale inventory, "
                "what to liquidate, or what's sitting idle."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_decision",
            "description": (
                "Explains the agent's decision for a specific SKU in plain language: why "
                "it's recommended to order or not, what data was used. "
                "Call this when the user asks 'why', 'explain the decision', "
                "or 'why order' for a specific SKU."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Product SKU",
                    }
                },
                "required": ["sku"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are Stocky, a smart AI assistant for warehouse and procurement management. "
    "You help buyers and business owners make daily decisions.\n\n"
    "## Rules\n"
    "- Respond in English, concisely and to the point.\n"
    "- Use available tools to get real data before answering.\n"
    "- Never fabricate SKUs, numbers, suppliers, or actions.\n"
    "- If the user mentions a specific SKU, use it in the tools.\n"
    "- If the user refers to 'this product' or 'it', use the SKU from "
    "the conversation context (last_resolved_sku).\n"
    "- If multiple tools are needed, call them sequentially.\n"
    "- When you have all the data, give a clear answer with a recommendation.\n"
    "- For general questions, start with analyze_full_catalog.\n"
    "- For questions about a specific SKU, use get_item_deep_dive.\n"
    "- For questions about dead stock, use flag_dead_stock.\n"
    "- For questions about purchasing, use build_purchase_order.\n"
    "- Be friendly and professional.\n\n"
    "## Response formatting\n"
    "You MUST format your response in Markdown. Follow these rules strictly:\n"
    "- Use **bold text** for key figures, SKUs, and statuses.\n"
    "- Separate logical blocks with a blank line (two line breaks).\n"
    "- For lists, use bullet points (- item).\n"
    "- For sequential steps or rankings, use numbered lists (1. item).\n"
    "- Use ### headings for sections if the response covers more than one topic.\n"
    "- For important warnings, use > blockquotes.\n"
    "- Wrap numbers, amounts, and SKUs in `code` for visual emphasis.\n"
    "- NEVER write long paragraphs of continuous text — break them into short bullet points.\n"
    "- Leave a blank line between sections.\n"
    "- Do not use # and ## headings, only ### and ####.\n"
)

# ---------------------------------------------------------------------------
# SKU resolution helpers
# ---------------------------------------------------------------------------


def _extract_sku(message: str, known_skus: list[str]) -> str | None:
    tokens = []
    for raw_token in message.replace("/", " ").replace(",", " ").split():
        token = raw_token.strip().upper().strip('.?!:;()[]{}"')
        if len(token) >= 3:
            tokens.append(token)

    for token in tokens:
        if token in known_skus:
            return token

    for token in tokens:
        matches = get_close_matches(token, known_skus, n=1, cutoff=0.85)
        if matches:
            return matches[0]

    return None


def _lookup_known_skus(db: Session) -> list[str]:
    return list(db.scalars(select(Product.sku).order_by(Product.sku)).all())


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("/", " ").split())


def _extract_product_name_match(db: Session, message: str) -> tuple[str, str] | None:
    normalized_message = _normalize_text(message)
    if len(normalized_message) < 4:
        return None

    statement = select(Product.sku, Product.name).where(Product.is_active.is_(True))
    rows = db.execute(statement).all()

    direct_matches: list[tuple[str, str, int]] = []
    fuzzy_candidates: list[tuple[str, str, float]] = []

    for sku, name in rows:
        normalized_name = _normalize_text(name)
        if len(normalized_name) < 3:
            continue

        if normalized_name in normalized_message:
            direct_matches.append((sku, name, len(normalized_name)))
            continue

        message_tokens = set(normalized_message.split())
        name_tokens = [token for token in normalized_name.split() if len(token) >= 3]
        overlap = sum(1 for token in name_tokens if token in message_tokens)
        if overlap >= 2:
            score = overlap / max(len(name_tokens), 1)
            fuzzy_candidates.append((sku, name, score))

    if direct_matches:
        direct_matches.sort(key=lambda item: item[2], reverse=True)
        sku, name, _ = direct_matches[0]
        return sku, name

    if fuzzy_candidates:
        fuzzy_candidates.sort(key=lambda item: item[2], reverse=True)
        sku, name, score = fuzzy_candidates[0]
        if score >= 0.5:
            return sku, name

    return None


def _resolve_product_reference(
    db: Session,
    message: str,
    known_skus: list[str],
    last_resolved_sku: str | None,
) -> tuple[str | None, str | None]:
    explicit_sku = _extract_sku(message, known_skus)
    if explicit_sku:
        return explicit_sku, None

    product_match = _extract_product_name_match(db, message)
    if product_match:
        return product_match

    return last_resolved_sku, None


def _should_include_known_skus(message: str, explicit_sku: str | None) -> bool:
    if explicit_sku:
        return False

    lowered = message.lower()
    return any(
        phrase in lowered
        for phrase in [
            "sku",
            "article",
            "product",
            "item",
            "which product",
            "find",
            "show product",
        ]
    )


def _log_step(conv_id: str, step: str, start_ts: float, **extra: Any) -> None:
    elapsed_ms = round((time.perf_counter() - start_ts) * 1000, 1)
    payload = {"conversation_id": conv_id, "step": step, "elapsed_ms": elapsed_ms}
    payload.update(extra)
    logger.info("chat_step %s", json.dumps(payload, ensure_ascii=False, default=str))


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ToolCallResult:
    tool_name: str
    tool_call_id: str
    args: dict[str, Any]
    result: dict[str, Any]
    error: str | None = None


def _execute_tool(db: Session, tool_call: LLMToolCallRequest) -> ToolCallResult:
    name = tool_call.function_name
    args = tool_call.arguments

    try:
        if name == "analyze_full_catalog":
            result = analyze_full_catalog(db)
        elif name == "get_item_deep_dive":
            sku = args.get("sku", "")
            result = get_item_deep_dive(db, sku)
            if result is None:
                result = {"error": f"SKU '{sku}' not found"}
        elif name == "forecast_demand":
            sku = args.get("sku", "")
            result = forecast_demand(db, sku)
            if result is None:
                result = {"error": f"SKU '{sku}' not found"}
        elif name == "build_purchase_order":
            supplier_id = args.get("supplier_id")
            result = build_purchase_order(db, supplier_id=supplier_id)
        elif name == "flag_dead_stock":
            result = flag_dead_stock(db)
        elif name == "explain_decision":
            sku = args.get("sku", "")
            result = explain_decision_for_sku(db, sku)
            if result is None:
                result = {"error": f"SKU '{sku}' not found"}
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as exc:
        logger.exception("Tool execution error for %s", name)
        result = {"error": str(exc)}

    return ToolCallResult(
        tool_name=name,
        tool_call_id=tool_call.id,
        args=args,
        result=result,
    )


def _execute_tool_batch(
    db: Session, tool_calls: list[LLMToolCallRequest], conv_id: str | None = None
) -> list[ToolCallResult]:
    if len(tool_calls) <= 1:
        single_results: list[ToolCallResult] = []
        for tool_call in tool_calls:
            started = time.perf_counter()
            result = _execute_tool(db, tool_call)
            if conv_id:
                _log_step(
                    conv_id,
                    "tool_executed",
                    started,
                    tool_name=result.tool_name,
                    parallel=False,
                )
            single_results.append(result)
        return single_results

    results_by_id: dict[str, ToolCallResult] = {}
    with ThreadPoolExecutor(
        max_workers=min(MAX_PARALLEL_TOOL_CALLS, len(tool_calls))
    ) as executor:
        futures = {}
        for tool_call in tool_calls:
            started = time.perf_counter()
            future = executor.submit(_execute_tool, db, tool_call)
            futures[future] = (tool_call, started)

        for future in as_completed(futures):
            tool_call, started = futures[future]
            result = future.result()
            results_by_id[tool_call.id] = result
            if conv_id:
                _log_step(
                    conv_id,
                    "tool_executed",
                    started,
                    tool_name=result.tool_name,
                    parallel=True,
                )

    return [
        results_by_id[tool_call.id]
        for tool_call in tool_calls
        if tool_call.id in results_by_id
    ]


# ---------------------------------------------------------------------------
# Result summarizers (to keep context window manageable)
# ---------------------------------------------------------------------------


def _summarize_for_context(tool_name: str, result: dict[str, Any]) -> dict[str, Any]:
    """Return a condensed version suitable for injecting back into LLM context."""
    if tool_name == "analyze_full_catalog":
        return {
            "summary": result.get("summary"),
            "traffic_light": result.get("traffic_light"),
            "top_critical": result.get("top_critical", [])[:5],
        }
    if tool_name == "build_purchase_order":
        orders = result.get("purchase_orders", [])
        trimmed_orders = []
        for order in orders[:3]:
            trimmed_orders.append(
                {
                    "supplier": order.get("supplier"),
                    "totals": order.get("totals"),
                    "items": order.get("items", [])[:5],
                }
            )
        return {
            "summary": result.get("summary"),
            "purchase_orders": trimmed_orders,
        }
    if tool_name == "flag_dead_stock":
        return {
            "summary": result.get("summary"),
            "items": result.get("items", [])[:7],
        }
    if tool_name == "get_item_deep_dive":
        return {
            "product": result.get("product"),
            "stock": result.get("stock"),
            "trend": result.get("trend"),
            "forecast": result.get("forecast"),
            "recommendation": result.get("recommendation"),
            "explanation": result.get("explanation"),
        }
    if tool_name == "explain_decision":
        return {
            "sku": result.get("sku"),
            "decision": result.get("decision"),
        }
    return result


def _summarize_for_frontend(tool_name: str, result: dict[str, Any]) -> dict[str, Any]:
    """Return a version suitable for frontend rendering (richer cards)."""
    if tool_name == "analyze_full_catalog":
        return {
            "summary": result.get("summary"),
            "traffic_light": result.get("traffic_light"),
            "top_critical": result.get("top_critical", [])[:5],
            "ranked_items": result.get("ranked_items", [])[:10],
        }
    if tool_name == "build_purchase_order":
        return {
            "summary": result.get("summary"),
            "purchase_orders": result.get("purchase_orders", [])[:3],
        }
    if tool_name == "flag_dead_stock":
        return {
            "summary": result.get("summary"),
            "items": result.get("items", [])[:10],
        }
    if tool_name == "get_item_deep_dive":
        return {
            "product": result.get("product"),
            "stock": result.get("stock"),
            "sales": result.get("sales"),
            "trend": result.get("trend"),
            "forecast": result.get("forecast"),
            "recommendation": result.get("recommendation"),
            "explanation": result.get("explanation"),
        }
    if tool_name == "forecast_demand":
        return result
    if tool_name == "explain_decision":
        return result
    return result


# ---------------------------------------------------------------------------
# Autonomous agentic loop (LLM path)
# ---------------------------------------------------------------------------


def _run_agentic_loop(
    db: Session,
    conversation_id: str,
    user_message: str,
    known_skus: list[str],
    last_resolved_sku: str | None,
) -> dict[str, Any]:
    """Run the LLM-powered agentic loop with tool calling."""

    provider = get_llm_provider()

    conversation = conversation_store.get(conversation_id)
    history_messages: list[LLMMessage] = []

    # System message
    system_content = SYSTEM_PROMPT
    if last_resolved_sku:
        system_content += f"\nContext: last discussed SKU = {last_resolved_sku}\n"
    explicit_sku = _extract_sku(user_message, known_skus)
    resolved_sku_hint, matched_product_name = _resolve_product_reference(
        db, user_message, known_skus, last_resolved_sku
    )
    if matched_product_name and resolved_sku_hint:
        system_content += f"\nProduct recognized by name: {matched_product_name} -> SKU {resolved_sku_hint}\n"
    if known_skus and _should_include_known_skus(user_message, explicit_sku):
        sku_sample = known_skus[:30]
        system_content += f"\nKnown SKUs (sample): {', '.join(sku_sample)}\n"
    history_messages.append(LLMMessage(role="system", content=system_content))

    # Replay conversation history (already includes current user message)
    if conversation:
        for entry in conversation.messages:
            msg = LLMMessage(
                role=entry.role,
                content=entry.content,
                tool_calls=entry.tool_calls_raw,
                tool_call_id=entry.tool_call_id,
                name=entry.name,
            )
            history_messages.append(msg)

    all_tool_results: list[ToolCallResult] = []
    iteration = 0

    while iteration < MAX_TOOL_ITERATIONS:
        iteration += 1

        try:
            llm_started = time.perf_counter()
            completion = provider.complete(
                messages=history_messages,
                temperature=0.2,
                tools=TOOL_DEFINITIONS,
            )
            _log_step(
                conversation_id,
                "llm_complete",
                llm_started,
                iteration=iteration,
                tool_calls=len(completion.tool_calls),
            )
        except Exception as exc:
            logger.exception("LLM completion failed at iteration %d", iteration)
            # Fall back to deterministic
            return _run_fallback(
                db, conversation_id, user_message, known_skus, last_resolved_sku
            )

        if completion.has_tool_calls:
            # Build the assistant message with tool_calls for the context
            raw_tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function_name,
                        "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                    },
                }
                for tc in completion.tool_calls
            ]

            assistant_tc_msg = LLMMessage(
                role="assistant",
                content=completion.content,
                tool_calls=raw_tool_calls,
            )
            history_messages.append(assistant_tc_msg)
            conversation_store.append(
                conversation_id,
                ConversationEntry(
                    role="assistant",
                    content=completion.content,
                    tool_calls_raw=raw_tool_calls,
                ),
            )

            # Execute each tool call
            tool_results = _execute_tool_batch(
                db, completion.tool_calls, conversation_id
            )
            for tc, tool_result in zip(completion.tool_calls, tool_results):
                all_tool_results.append(tool_result)

                # Track resolved SKU
                if tc.function_name in (
                    "get_item_deep_dive",
                    "forecast_demand",
                    "explain_decision",
                ):
                    resolved_sku = tc.arguments.get("sku")
                    if resolved_sku:
                        conversation_store.set_last_sku(conversation_id, resolved_sku)

                # Add tool result message to context
                summarized = _summarize_for_context(
                    tool_result.tool_name, tool_result.result
                )
                tool_result_content = json.dumps(
                    summarized, ensure_ascii=False, default=str
                )

                tool_msg = LLMMessage(
                    role="tool",
                    content=tool_result_content,
                    tool_call_id=tc.id,
                    name=tc.function_name,
                )
                history_messages.append(tool_msg)
                conversation_store.append(
                    conversation_id,
                    ConversationEntry(
                        role="tool",
                        content=tool_result_content,
                        tool_call_id=tc.id,
                        name=tc.function_name,
                    ),
                )
        else:
            # LLM returned a final text response
            final_text = completion.content or ""

            conversation_store.append(
                conversation_id,
                ConversationEntry(role="assistant", content=final_text),
            )

            return {
                "reply": {
                    "source": "llm",
                    "provider": completion.provider,
                    "model": completion.model,
                    "text": final_text,
                },
                "tool_calls": [
                    {
                        "tool_name": tr.tool_name,
                        "args": tr.args,
                        "result": _summarize_for_frontend(tr.tool_name, tr.result),
                    }
                    for tr in all_tool_results
                ],
            }

    # If we hit the max iterations, force a final answer
    history_messages.append(
        LLMMessage(
            role="user",
            content="Please formulate a final answer based on the collected data.",
        )
    )

    try:
        final_completion = provider.complete(messages=history_messages, temperature=0.2)
        final_text = final_completion.content or ""
    except Exception:
        final_text = _build_deterministic_reply(all_tool_results)

    conversation_store.append(
        conversation_id,
        ConversationEntry(role="assistant", content=final_text),
    )

    return {
        "reply": {
            "source": "llm",
            "provider": "openrouter",
            "model": settings.openrouter_model,
            "text": final_text,
        },
        "tool_calls": [
            {
                "tool_name": tr.tool_name,
                "args": tr.args,
                "result": _summarize_for_frontend(tr.tool_name, tr.result),
            }
            for tr in all_tool_results
        ],
    }


# ---------------------------------------------------------------------------
# Fallback: rule-based routing (no LLM)
# ---------------------------------------------------------------------------


def _run_fallback(
    db: Session,
    conversation_id: str,
    user_message: str,
    known_skus: list[str],
    last_resolved_sku: str | None,
) -> dict[str, Any]:
    """Rule-based tool selection when LLM is unavailable."""
    lowered = user_message.lower()

    sku = _extract_sku(user_message, known_skus) or last_resolved_sku

    tool_results: list[ToolCallResult] = []

    wants_overview = any(
        p in lowered
        for p in [
            "catalog",
            "overview",
            "critical",
            "what's happening",
            "what is urgent",
            "warehouse",
            "all products",
            "all items",
        ]
    )
    wants_dead_stock = any(
        p in lowered
        for p in [
            "dead stock",
            "dead-stock",
            "stale",
            "idle",
            "liquidate",
            "clearance",
            "discount",
        ]
    )
    wants_purchase = any(
        p in lowered
        for p in [
            "purchase",
            "order",
            "procurement",
            "supplier",
            "what to order",
            "purchase plan",
        ]
    )
    wants_forecast = any(p in lowered for p in ["forecast", "demand", "trend"])
    wants_explain = any(p in lowered for p in ["why", "explain", "reason"])

    # Execute tools based on intent
    if sku and wants_explain:
        result = explain_decision_for_sku(db, sku)
        if result:
            tool_results.append(
                ToolCallResult("explain_decision", "", {"sku": sku}, result)
            )

    if sku and (
        wants_forecast or wants_explain or "sku" in lowered or "product" in lowered
    ):
        result = get_item_deep_dive(db, sku)
        if result:
            tool_results.append(
                ToolCallResult("get_item_deep_dive", "", {"sku": sku}, result)
            )
            conversation_store.set_last_sku(conversation_id, sku)

    if sku and wants_forecast:
        result = forecast_demand(db, sku)
        if result:
            tool_results.append(
                ToolCallResult("forecast_demand", "", {"sku": sku}, result)
            )

    if wants_dead_stock:
        result = flag_dead_stock(db)
        tool_results.append(ToolCallResult("flag_dead_stock", "", {}, result))

    if wants_overview or wants_purchase:
        result = analyze_full_catalog(db)
        tool_results.append(ToolCallResult("analyze_full_catalog", "", {}, result))

    if wants_purchase:
        result = build_purchase_order(db)
        tool_results.append(ToolCallResult("build_purchase_order", "", {}, result))

    if not tool_results:
        if sku:
            result = get_item_deep_dive(db, sku)
            if result:
                tool_results.append(
                    ToolCallResult("get_item_deep_dive", "", {"sku": sku}, result)
                )
                conversation_store.set_last_sku(conversation_id, sku)
        if not tool_results:
            result = analyze_full_catalog(db)
            tool_results.append(ToolCallResult("analyze_full_catalog", "", {}, result))

    reply_text = _build_deterministic_reply(tool_results)

    conversation_store.append(
        conversation_id,
        ConversationEntry(role="assistant", content=reply_text),
    )

    return {
        "reply": {
            "source": "deterministic",
            "provider": None,
            "model": None,
            "text": reply_text,
        },
        "tool_calls": [
            {
                "tool_name": tr.tool_name,
                "args": tr.args,
                "result": _summarize_for_frontend(tr.tool_name, tr.result),
            }
            for tr in tool_results
        ],
    }


def _build_deterministic_reply(tool_results: list[ToolCallResult]) -> str:
    parts: list[str] = []

    for tr in tool_results:
        result = tr.result

        if "error" in result:
            parts.append(f"> Error calling `{tr.tool_name}`: {result['error']}")
            continue

        if tr.tool_name == "analyze_full_catalog":
            s = result.get("summary", {})
            parts.append(
                f"### Catalog Overview\n\n"
                f"- **Critical:** `{s.get('critical_count', 0)}` SKUs\n"
                f"- **Warning:** `{s.get('warning_count', 0)}` SKUs\n"
                f"- **Stable:** `{s.get('ok_count', 0)}` SKUs"
            )

        elif tr.tool_name == "flag_dead_stock":
            s = result.get("summary", {})
            parts.append(
                f"### Dead Stock\n\n"
                f"Found **{s.get('items_count', 0)}** items "
                f"with a total value of **{s.get('total_stock_value', 0)}**."
            )

        elif tr.tool_name == "build_purchase_order":
            s = result.get("summary", {})
            parts.append(
                f"### Purchase Plan\n\n"
                f"- **Items:** `{s.get('items_count', 0)}`\n"
                f"- **Suppliers:** `{s.get('suppliers_count', 0)}`\n"
                f"- **Total:** `{s.get('grand_total', 0)}`"
            )

        elif tr.tool_name == "forecast_demand":
            fc = result.get("forecast", {})
            sku = result.get("sku", "?")
            parts.append(
                f"### Forecast for `{sku}`\n\n"
                f"- **7 days:** `{fc.get('forecast_7d', '?')}`\n"
                f"- **14 days:** `{fc.get('forecast_14d', '?')}`\n"
                f"- **30 days:** `{fc.get('forecast_30d', '?')}`"
            )

        elif tr.tool_name == "get_item_deep_dive":
            rec = result.get("recommendation", {})
            product = result.get("product", {})
            stock = result.get("stock", {})
            explanation = result.get("explanation", {})
            sku = product.get("sku", "?")
            parts.append(
                f"### Analysis of `{sku}`\n\n"
                f"- **Stock:** `{stock.get('available_qty', '?')}`\n"
                f"- **Status:** **{stock.get('status', '?')}**\n"
                f"- **Recommended order:** `{rec.get('recommended_order_qty', 0)}`"
            )
            if explanation.get("text"):
                parts.append(f"\n{explanation['text']}")

        elif tr.tool_name == "explain_decision":
            decision = result.get("decision", {})
            if decision.get("text"):
                parts.append(decision["text"])

    if not parts:
        return (
            "I can help with:\n\n"
            "- **Warehouse analysis** — general catalog overview\n"
            "- **Demand forecast** — for a specific SKU\n"
            "- **Dead stock detection** — stale inventory items\n"
            "- **Purchase plan** — what to order\n\n"
            'Try asking, for example: "What should we order this week?"'
        )

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def chat_with_agent(
    db: Session,
    message: str,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    request_started = time.perf_counter()
    clean_message = message.strip()

    conversation = conversation_store.get_or_create(conversation_id)
    conv_id = conversation.id
    sku_lookup_started = time.perf_counter()
    known_skus = _lookup_known_skus(db)
    _log_step(conv_id, "sku_lookup", sku_lookup_started, sku_count=len(known_skus))

    # Resolve SKU from message or memory
    explicit_sku = _extract_sku(clean_message, known_skus)
    last_sku = conversation_store.get_last_sku(conv_id)
    resolved_sku, matched_product_name = _resolve_product_reference(
        db, clean_message, known_skus, last_sku
    )

    if resolved_sku:
        conversation_store.set_last_sku(conv_id, resolved_sku)

    # Save user message to memory
    conversation_store.append(
        conv_id, ConversationEntry(role="user", content=clean_message)
    )
    _log_step(
        conv_id,
        "user_message_stored",
        request_started,
        explicit_sku=explicit_sku,
        resolved_sku=resolved_sku,
        matched_product_name=matched_product_name,
    )

    # Choose execution path
    if settings.openrouter_enabled:
        try:
            result = _run_agentic_loop(
                db, conv_id, clean_message, known_skus, resolved_sku
            )
        except Exception:
            logger.exception("Agentic loop failed, falling back to deterministic")
            result = _run_fallback(db, conv_id, clean_message, known_skus, resolved_sku)
    else:
        result = _run_fallback(db, conv_id, clean_message, known_skus, resolved_sku)

    _log_step(
        conv_id,
        "request_completed",
        request_started,
        path=result["reply"].get("source"),
    )

    return {
        "conversation_id": conv_id,
        "message": clean_message,
        "resolved_sku": resolved_sku,
        **result,
    }


# ---------------------------------------------------------------------------
# Streaming entry point (SSE)
# ---------------------------------------------------------------------------


def chat_with_agent_stream(
    db: Session,
    message: str,
    conversation_id: str | None = None,
):
    """Generator that yields SSE-formatted events for streaming chat.

    Events:
      event: meta      — conversation metadata + tool_calls (JSON)
      event: token     — single text token delta
      event: done      — stream finished
      event: error     — error occurred
    """
    request_started = time.perf_counter()
    clean_message = message.strip()

    conversation = conversation_store.get_or_create(conversation_id)
    conv_id = conversation.id
    sku_lookup_started = time.perf_counter()
    known_skus = _lookup_known_skus(db)
    _log_step(conv_id, "sku_lookup", sku_lookup_started, sku_count=len(known_skus))

    explicit_sku = _extract_sku(clean_message, known_skus)
    last_sku = conversation_store.get_last_sku(conv_id)
    resolved_sku, matched_product_name = _resolve_product_reference(
        db, clean_message, known_skus, last_sku
    )

    if resolved_sku:
        conversation_store.set_last_sku(conv_id, resolved_sku)

    conversation_store.append(
        conv_id, ConversationEntry(role="user", content=clean_message)
    )
    _log_step(
        conv_id,
        "user_message_stored",
        request_started,
        explicit_sku=explicit_sku,
        resolved_sku=resolved_sku,
        matched_product_name=matched_product_name,
    )

    # Helper to build SSE lines.
    # SSE spec: newlines inside data must be sent as separate "data:" lines,
    # OR the payload must be JSON-encoded on a single line.
    def _sse_raw(event: str, data: str) -> str:
        """Send pre-serialised JSON (e.g. meta object) as-is."""
        return f"event: {event}\ndata: {data}\n\n"

    def _sse(event: str, data: str) -> str:
        """JSON-encode the value so newlines in Markdown survive SSE transport."""
        safe = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {safe}\n\n"

    # --- Fallback path (no streaming, send all at once) ---
    if not settings.openrouter_enabled:
        result = _run_fallback(db, conv_id, clean_message, known_skus, resolved_sku)
        meta = json.dumps(
            {
                "conversation_id": conv_id,
                "resolved_sku": resolved_sku,
                "tool_calls": result.get("tool_calls", []),
            },
            ensure_ascii=False,
            default=str,
        )
        yield _sse_raw("meta", meta)
        yield _sse("token", result["reply"]["text"])
        yield _sse("done", "")
        return

    # --- LLM path: run tool loop, then stream final answer ---
    try:
        provider = get_llm_provider()

        conv = conversation_store.get(conv_id)
        history_messages: list[LLMMessage] = []

        system_content = SYSTEM_PROMPT
        if resolved_sku:
            system_content += f"\nContext: last discussed SKU = {resolved_sku}\n"
        if matched_product_name and resolved_sku:
            system_content += f"\nProduct recognized by name: {matched_product_name} -> SKU {resolved_sku}\n"
        if known_skus and _should_include_known_skus(clean_message, explicit_sku):
            sku_sample = known_skus[:30]
            system_content += f"\nKnown SKUs (sample): {', '.join(sku_sample)}\n"
        history_messages.append(LLMMessage(role="system", content=system_content))
        _log_step(
            conv_id,
            "context_built",
            request_started,
            history_size=len(conv.messages) if conv else 0,
        )

        if conv:
            for entry in conv.messages:
                history_messages.append(
                    LLMMessage(
                        role=entry.role,
                        content=entry.content,
                        tool_calls=entry.tool_calls_raw,
                        tool_call_id=entry.tool_call_id,
                        name=entry.name,
                    )
                )

        all_tool_results: list[ToolCallResult] = []
        iteration = 0

        # Tool-calling loop (non-streaming)
        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            try:
                llm_started = time.perf_counter()
                completion = provider.complete(
                    messages=history_messages,
                    temperature=0.2,
                    tools=TOOL_DEFINITIONS,
                )
                _log_step(
                    conv_id,
                    "llm_complete",
                    llm_started,
                    iteration=iteration,
                    tool_calls=len(completion.tool_calls),
                )
            except Exception:
                logger.exception("LLM completion failed at iteration %d", iteration)
                result = _run_fallback(
                    db, conv_id, clean_message, known_skus, resolved_sku
                )
                meta = json.dumps(
                    {
                        "conversation_id": conv_id,
                        "resolved_sku": resolved_sku,
                        "tool_calls": result.get("tool_calls", []),
                    },
                    ensure_ascii=False,
                    default=str,
                )
                yield _sse_raw("meta", meta)
                yield _sse("token", result["reply"]["text"])
                yield _sse("done", "")
                return

            if not completion.has_tool_calls:
                break  # ready for streaming final answer

            # Execute tool calls
            raw_tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function_name,
                        "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                    },
                }
                for tc in completion.tool_calls
            ]

            assistant_tc_msg = LLMMessage(
                role="assistant",
                content=completion.content,
                tool_calls=raw_tool_calls,
            )
            history_messages.append(assistant_tc_msg)
            conversation_store.append(
                conv_id,
                ConversationEntry(
                    role="assistant",
                    content=completion.content,
                    tool_calls_raw=raw_tool_calls,
                ),
            )

            tool_results = _execute_tool_batch(db, completion.tool_calls, conv_id)
            for tc, tool_result in zip(completion.tool_calls, tool_results):
                all_tool_results.append(tool_result)

                if tc.function_name in (
                    "get_item_deep_dive",
                    "forecast_demand",
                    "explain_decision",
                ):
                    sku_val = tc.arguments.get("sku")
                    if sku_val:
                        conversation_store.set_last_sku(conv_id, sku_val)

                summarized = _summarize_for_context(
                    tool_result.tool_name, tool_result.result
                )
                tool_result_content = json.dumps(
                    summarized, ensure_ascii=False, default=str
                )
                tool_msg = LLMMessage(
                    role="tool",
                    content=tool_result_content,
                    tool_call_id=tc.id,
                    name=tc.function_name,
                )
                history_messages.append(tool_msg)
                conversation_store.append(
                    conv_id,
                    ConversationEntry(
                        role="tool",
                        content=tool_result_content,
                        tool_call_id=tc.id,
                        name=tc.function_name,
                    ),
                )
        else:
            # Hit max iterations — force final answer
            history_messages.append(
                LLMMessage(
                    role="user",
                    content="Please formulate a final answer based on the collected data.",
                )
            )

        # Emit meta with tool_calls
        frontend_tool_calls = [
            {
                "tool_name": tr.tool_name,
                "args": tr.args,
                "result": _summarize_for_frontend(tr.tool_name, tr.result),
            }
            for tr in all_tool_results
        ]
        meta = json.dumps(
            {
                "conversation_id": conv_id,
                "resolved_sku": resolved_sku,
                "tool_calls": frontend_tool_calls,
            },
            ensure_ascii=False,
            default=str,
        )
        yield _sse_raw("meta", meta)
        _log_step(
            conv_id,
            "meta_emitted",
            request_started,
            tool_calls=len(frontend_tool_calls),
        )

        # Stream final LLM response token by token
        collected_text = ""
        try:
            stream_started = time.perf_counter()
            for token in provider.stream_complete(
                messages=history_messages, temperature=0.2
            ):
                if not collected_text:
                    _log_step(conv_id, "first_token", stream_started)
                collected_text += token
                yield _sse("token", token)
        except Exception:
            logger.exception("Streaming failed, falling back")
            if not collected_text:
                collected_text = _build_deterministic_reply(all_tool_results)
                yield _sse("token", collected_text)

        conversation_store.append(
            conv_id, ConversationEntry(role="assistant", content=collected_text)
        )
        _log_step(
            conv_id,
            "stream_completed",
            request_started,
            response_chars=len(collected_text),
        )
        yield _sse("done", "")

    except Exception as exc:
        logger.exception("Stream error")
        yield _sse("error", str(exc))

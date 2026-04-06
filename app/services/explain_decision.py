from __future__ import annotations

from app.core.config import settings
from app.llm import get_llm_provider
from app.llm.base import LLMMessage
from app.services.get_item_deep_dive import get_item_deep_dive


def _deterministic_decision_text(payload: dict) -> str:
    product = payload["product"]
    stock = payload["stock"]
    trend = payload["trend"]
    forecast = payload["forecast"]
    recommendation = payload["recommendation"]

    if recommendation["recommended_order_qty"] > 0:
        return (
            f"The decision for SKU {product['sku']} is based on the available stock of {stock['available_qty']} "
            f"being sufficient for approximately {stock['days_of_stock']} days, while the lead time is {product['lead_time_days']} days "
            f"and the safety buffer is {product['safety_stock_days']} days. The 14-day forecast is {forecast['forecast_14d']}, "
            f"and the demand trend is assessed as {trend['label']}. Therefore, the system recommends ordering {recommendation['recommended_order_qty']} {product['unit']}"
            f" considering the minimum order quantity of {product['min_order_qty']}."
        )

    return (
        f"For SKU {product['sku']}, no new purchase is currently required. The available stock of {stock['available_qty']} is sufficient for approximately {stock['days_of_stock']} days, "
        f"and the 14-day forecast is {forecast['forecast_14d']}. The demand trend is currently {trend['label']}, so the agent considers the current stock sufficient without reordering."
    )


def explain_decision(payload: dict) -> dict:
    deterministic_text = _deterministic_decision_text(payload)
    inputs_used = {
        "available_qty": payload["stock"]["available_qty"],
        "days_of_stock": payload["stock"]["days_of_stock"],
        "lead_time_days": payload["product"]["lead_time_days"],
        "safety_stock_days": payload["product"]["safety_stock_days"],
        "forecast_14d": payload["forecast"]["forecast_14d"],
        "trend_label": payload["trend"]["label"],
        "recommended_order_qty": payload["recommendation"]["recommended_order_qty"],
    }
    if not settings.openrouter_enabled:
        return {
            "source": "deterministic",
            "provider": None,
            "model": None,
            "text": deterministic_text,
            "inputs_used": inputs_used,
            "error": None,
        }

    prompt = (
        "You explain the warehouse AI agent's decision to a procurement manager in clear, professional English. "
        "Briefly explain why the system arrived at this particular conclusion. "
        "Do not invent new data, use only the provided payload. Respond in 3-5 sentences in English.\n\n"
        f"Payload: {payload}"
    )

    try:
        provider = get_llm_provider()
        result = provider.complete(
            [
                LLMMessage(
                    role="system",
                    content="You explain inventory agent decisions to humans.",
                ),
                LLMMessage(role="user", content=prompt),
            ],
            temperature=0.1,
        )
        return {
            "source": "llm",
            "provider": result.provider,
            "model": result.model,
            "text": result.content,
            "fallback_text": deterministic_text,
            "inputs_used": inputs_used,
            "error": result.error,
        }
    except Exception as exc:
        return {
            "source": "deterministic",
            "provider": None,
            "model": None,
            "text": deterministic_text,
            "inputs_used": inputs_used,
            "error": str(exc),
        }


def explain_decision_for_sku(db, sku: str) -> dict | None:
    payload = get_item_deep_dive(db, sku)
    if payload is None:
        return None
    return {
        "sku": sku,
        "decision": explain_decision(payload),
        "context": {
            "product": payload["product"],
            "stock": payload["stock"],
            "trend": payload["trend"],
            "forecast": payload["forecast"],
            "recommendation": payload["recommendation"],
        },
    }

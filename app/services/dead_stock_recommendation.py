from __future__ import annotations

from app.services.explain_decision import explain_decision
from app.services.flag_dead_stock import flag_dead_stock
from app.services.get_item_deep_dive import get_item_deep_dive
from app.services.workflow_utils import make_tool_call


def get_dead_stock_recommendation(db) -> dict:
    dead_stock = flag_dead_stock(db)
    focus_items = dead_stock["items"][:5]

    deep_dives = []
    explanations = []
    for item in focus_items:
        deep_dive = get_item_deep_dive(db, item["sku"])
        if deep_dive is None:
            continue
        deep_dives.append(deep_dive)
        explanations.append(
            {
                "sku": item["sku"],
                "decision": explain_decision(deep_dive),
                "dead_stock_action": item["recommended_action"],
            }
        )

    workflow_steps = [
        make_tool_call(
            1,
            "flag_dead_stock",
            "completed",
            dead_stock["summary"],
        ),
        make_tool_call(
            2,
            "get_item_deep_dive",
            "completed",
            {
                "processed_skus": [item["product"]["sku"] for item in deep_dives],
                "deep_dives_count": len(deep_dives),
            },
        ),
        make_tool_call(
            3,
            "explain_decision",
            "completed",
            {
                "explained_skus": [item["sku"] for item in explanations],
                "explanations_count": len(explanations),
            },
        ),
    ]

    return {
        "question": "What should I discount, promote, or stop reordering?",
        "summary": dead_stock["summary"],
        "workflow_steps": workflow_steps,
        "dead_stock_items": dead_stock["items"],
        "deep_dives": deep_dives,
        "decision_explanations": explanations,
    }

from __future__ import annotations

from datetime import date
from decimal import Decimal
import math

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.llm import get_llm_provider
from app.llm.base import LLMMessage
from app.models import Product
from app.models import ProductMetrics
from app.models import Stock
from app.models import Supplier
from app.services.forecast_demand import forecast_demand


def _to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _get_trend_label(trend_ratio: float) -> str:
    if trend_ratio > 1.15:
        return "accelerating"
    if trend_ratio < 0.85:
        return "decelerating"
    return "stable"


def _round_to_min_order(raw_qty: float, min_order_qty: int) -> float:
    if raw_qty <= 0:
        return 0.0
    return float(math.ceil(raw_qty / min_order_qty) * min_order_qty)


def _build_deterministic_explanation(payload: dict) -> str:
    product = payload["product"]
    stock = payload["stock"]
    forecast = payload["forecast"]
    recommendation = payload["recommendation"]
    trend = payload["trend"]

    if recommendation["recommended_order_qty"] > 0:
        return (
            f"SKU {product['sku']} ({product['name']}) requires close monitoring: "
            f"available stock is {stock['available_qty']}, coverage is approximately {stock['days_of_stock']} days, "
            f"with a lead time of {product['lead_time_days']} days and a safety buffer of {product['safety_stock_days']} days. "
            f"The current demand trend is {trend['label']}, and the 14-day forecast is {forecast['forecast_14d']}. "
            f"Therefore, it is recommended to order {recommendation['recommended_order_qty']} {product['unit']}"
            f" considering the minimum order quantity of {product['min_order_qty']}."
        )

    return (
        f"SKU {product['sku']} ({product['name']}) does not currently require a purchase: available stock is {stock['available_qty']}, "
        f"coverage is approximately {stock['days_of_stock']} days, and the 14-day forecast is {forecast['forecast_14d']}. "
        f"The demand trend is {trend['label']}, so the current stock is sufficient without a new order."
    )


def _build_llm_explanation(payload: dict) -> dict:
    deterministic_text = _build_deterministic_explanation(payload)
    if not settings.openrouter_enabled:
        return {
            "source": "deterministic",
            "provider": None,
            "model": None,
            "text": deterministic_text,
        }

    prompt = (
        "You are an inventory analyst. Briefly and clearly explain the SKU decision to a procurement manager in English. "
        "Do not invent new figures, use only the provided data. "
        "Respond in 3-5 sentences, professional tone, no filler.\n\n"
        f"Data: {payload}"
    )

    try:
        provider = get_llm_provider()
        result = provider.complete(
            [
                LLMMessage(
                    role="system",
                    content="You help procurement managers make warehouse decisions.",
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
        }
    except Exception:
        return {
            "source": "deterministic",
            "provider": None,
            "model": None,
            "text": deterministic_text,
        }


def get_item_deep_dive(db: Session, sku: str) -> dict | None:
    stock_subquery = (
        select(
            Stock.product_id.label("product_id"),
            func.coalesce(func.sum(Stock.quantity), 0).label("total_qty"),
            func.coalesce(func.sum(Stock.reserved_qty), 0).label("reserved_qty"),
            func.coalesce(func.sum(Stock.available_qty), 0).label("available_qty"),
        )
        .group_by(Stock.product_id)
        .subquery()
    )

    statement = (
        select(Product, Supplier.name, ProductMetrics, stock_subquery)
        .join(Supplier, Product.supplier_id == Supplier.id, isouter=True)
        .join(ProductMetrics, ProductMetrics.product_id == Product.id, isouter=True)
        .join(stock_subquery, stock_subquery.c.product_id == Product.id, isouter=True)
        .where(Product.sku == sku)
    )
    row = db.execute(statement).one_or_none()
    if row is None:
        return None

    product = row[0]
    supplier_name = row[1]
    metrics = row[2]
    today = date.today()
    forecast_payload = forecast_demand(db, sku)
    if forecast_payload is None:
        return None

    sales_7d = forecast_payload["inputs"]["sales_7d"]
    sales_30d = forecast_payload["inputs"]["sales_30d"]
    sales_90d = forecast_payload["inputs"]["sales_90d"]
    blended_velocity = forecast_payload["forecast"]["blended_velocity"]
    forecast_7d = forecast_payload["forecast"]["forecast_7d"]
    forecast_14d = forecast_payload["forecast"]["forecast_14d"]
    forecast_30d = forecast_payload["forecast"]["forecast_30d"]

    available_qty = float(row.available_qty or 0)
    total_qty = float(row.total_qty or 0)
    reserved_qty = float(row.reserved_qty or 0)
    lead_time_days = int(product.lead_time_days)
    safety_stock_days = int(product.safety_stock_days)
    min_order_qty = int(product.min_order_qty)
    coverage_days = (
        round(available_qty / blended_velocity, 1) if blended_velocity > 0 else None
    )
    target_stock = round(blended_velocity * (lead_time_days + safety_stock_days), 3)
    raw_order_qty = round(max(0.0, target_stock - available_qty), 3)
    recommended_order_qty = _round_to_min_order(raw_order_qty, min_order_qty)

    if product.max_stock_qty is not None:
        max_allowed = max(0.0, float(product.max_stock_qty) - available_qty)
        recommended_order_qty = min(recommended_order_qty, max_allowed)
        recommended_order_qty = (
            _round_to_min_order(recommended_order_qty, min_order_qty)
            if recommended_order_qty > 0
            else 0.0
        )

    trend_ratio = (
        round(sales_7d["avg_daily_sales"] / sales_30d["avg_daily_sales"], 3)
        if sales_30d["avg_daily_sales"] > 0
        else 1.0
    )
    trend_label = _get_trend_label(trend_ratio)

    payload = {
        "product": {
            "id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "subcategory": product.subcategory,
            "unit": product.unit,
            "supplier_name": supplier_name,
            "purchase_price": float(product.purchase_price)
            if product.purchase_price is not None
            else None,
            "selling_price": float(product.selling_price)
            if product.selling_price is not None
            else None,
            "lead_time_days": lead_time_days,
            "min_order_qty": min_order_qty,
            "safety_stock_days": safety_stock_days,
            "max_stock_qty": product.max_stock_qty,
        },
        "stock": {
            "total_qty": round(total_qty, 3),
            "reserved_qty": round(reserved_qty, 3),
            "available_qty": round(available_qty, 3),
            "days_of_stock": coverage_days,
            "status": metrics.status if metrics is not None else None,
            "reorder_point": metrics.reorder_point
            if metrics is not None
            else lead_time_days + safety_stock_days,
        },
        "sales": {
            "sales_7d": sales_7d,
            "sales_30d": sales_30d,
            "sales_90d": sales_90d,
            "last_sale_date": str(metrics.last_sale_date)
            if metrics is not None and metrics.last_sale_date is not None
            else None,
            "dead_stock_days": metrics.dead_stock_days if metrics is not None else None,
        },
        "trend": {
            "trend_ratio": trend_ratio,
            "label": trend_label,
        },
        "forecast": {
            "blended_velocity": blended_velocity,
            "forecast_7d": forecast_7d,
            "forecast_14d": forecast_14d,
            "forecast_30d": forecast_30d,
        },
        "recommendation": {
            "target_stock": target_stock,
            "raw_order_qty": raw_order_qty,
            "recommended_order_qty": round(recommended_order_qty, 3),
        },
    }
    payload["explanation"] = _build_llm_explanation(payload)
    return payload

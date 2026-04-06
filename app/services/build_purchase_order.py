from __future__ import annotations

from datetime import date, timedelta
import math

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product
from app.models import ProductMetrics
from app.models import ProductSupplier
from app.models import Stock
from app.models import Supplier
from app.services.forecast_demand import forecast_demand


def _round_up_to_pack(quantity: float, min_order_qty: int) -> float:
    if quantity <= 0:
        return 0.0
    if min_order_qty <= 1:
        return round(quantity, 3)
    return float(math.ceil(quantity / min_order_qty) * min_order_qty)


def build_purchase_order(db: Session, supplier_id: str | None = None) -> dict:
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

    primary_supplier_subquery = (
        select(
            ProductSupplier.product_id.label("product_id"),
            ProductSupplier.supplier_id.label("supplier_id"),
            ProductSupplier.purchase_price.label("supplier_purchase_price"),
            ProductSupplier.lead_time_days.label("supplier_lead_time_days"),
            ProductSupplier.min_order_qty.label("supplier_min_order_qty"),
            Supplier.name.label("supplier_name"),
            Supplier.min_order_amount.label("supplier_min_order_amount"),
            Supplier.payment_terms.label("payment_terms"),
        )
        .join(Supplier, Supplier.id == ProductSupplier.supplier_id)
        .where(ProductSupplier.is_primary.is_(True))
        .subquery()
    )

    statement = (
        select(Product, ProductMetrics, stock_subquery, primary_supplier_subquery)
        .join(ProductMetrics, ProductMetrics.product_id == Product.id, isouter=True)
        .join(stock_subquery, stock_subquery.c.product_id == Product.id, isouter=True)
        .join(
            primary_supplier_subquery,
            primary_supplier_subquery.c.product_id == Product.id,
            isouter=True,
        )
        .where(Product.is_active.is_(True))
        .order_by(Product.sku)
    )

    rows = db.execute(statement).all()
    supplier_groups: dict[str, dict] = {}

    for row in rows:
        product = row[0]
        metrics = row[1]
        current_supplier_id = row.supplier_id
        if current_supplier_id is None:
            continue
        if supplier_id is not None and str(current_supplier_id) != supplier_id:
            continue

        status = metrics.status if metrics is not None and metrics.status else "ok"
        if status not in {"critical", "warning"}:
            continue

        forecast_payload = forecast_demand(db, product.sku)
        if forecast_payload is None:
            continue

        available_qty = float(row.available_qty or 0)
        blended_velocity = float(forecast_payload["forecast"]["blended_velocity"])
        lead_time_days = int(row.supplier_lead_time_days or product.lead_time_days)
        min_order_qty = int(row.supplier_min_order_qty or product.min_order_qty)
        target_stock = blended_velocity * (
            lead_time_days + int(product.safety_stock_days)
        )
        metric_reorder_qty = (
            float(metrics.reorder_qty)
            if metrics is not None and metrics.reorder_qty is not None
            else 0.0
        )
        raw_order_qty = max(0.0, metric_reorder_qty, target_stock - available_qty)
        order_qty = _round_up_to_pack(raw_order_qty, min_order_qty)

        if product.max_stock_qty is not None:
            max_additional = max(0.0, float(product.max_stock_qty) - available_qty)
            order_qty = min(order_qty, max_additional)
            order_qty = (
                _round_up_to_pack(order_qty, min_order_qty) if order_qty > 0 else 0.0
            )

        if order_qty <= 0:
            continue

        purchase_price = float(
            row.supplier_purchase_price or product.purchase_price or 0
        )
        line_total = round(order_qty * purchase_price, 2)
        supplier_key = str(current_supplier_id)
        expected_delivery_date = str(date.today() + timedelta(days=lead_time_days))

        if supplier_key not in supplier_groups:
            supplier_groups[supplier_key] = {
                "supplier": {
                    "supplier_id": supplier_key,
                    "supplier_name": row.supplier_name,
                    "payment_terms": row.payment_terms,
                    "min_order_amount": float(row.supplier_min_order_amount or 0),
                    "expected_delivery_date": expected_delivery_date,
                },
                "items": [],
                "totals": {
                    "lines_count": 0,
                    "total_amount": 0.0,
                    "below_min_order_amount": False,
                },
            }

        supplier_groups[supplier_key]["items"].append(
            {
                "product_id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "category": product.category,
                "unit": product.unit,
                "status": status,
                "available_qty": round(available_qty, 3),
                "forecast_14d": forecast_payload["forecast"]["forecast_14d"],
                "target_stock": round(target_stock, 3),
                "raw_order_qty": round(raw_order_qty, 3),
                "order_qty": round(order_qty, 3),
                "min_order_qty": min_order_qty,
                "purchase_price": purchase_price,
                "line_total": line_total,
                "lead_time_days": lead_time_days,
                "reason": (
                    "Stock below safety coverage, replenishment needed"
                    if status == "critical"
                    else "Product approaching reorder threshold"
                ),
            }
        )

    purchase_orders = []
    for supplier_group in supplier_groups.values():
        total_amount = round(
            sum(item["line_total"] for item in supplier_group["items"]), 2
        )
        supplier_group["totals"]["lines_count"] = len(supplier_group["items"])
        supplier_group["totals"]["total_amount"] = total_amount
        supplier_group["totals"]["below_min_order_amount"] = (
            total_amount < supplier_group["supplier"]["min_order_amount"]
            if supplier_group["supplier"]["min_order_amount"] > 0
            else False
        )
        supplier_group["items"] = sorted(
            supplier_group["items"],
            key=lambda item: (item["status"] != "critical", -item["line_total"]),
        )
        purchase_orders.append(supplier_group)

    purchase_orders = sorted(
        purchase_orders,
        key=lambda order: order["totals"]["total_amount"],
        reverse=True,
    )

    return {
        "summary": {
            "suppliers_count": len(purchase_orders),
            "items_count": sum(
                order["totals"]["lines_count"] for order in purchase_orders
            ),
            "grand_total": round(
                sum(order["totals"]["total_amount"] for order in purchase_orders), 2
            ),
        },
        "purchase_orders": purchase_orders,
    }

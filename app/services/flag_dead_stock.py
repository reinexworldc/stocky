from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product
from app.models import ProductMetrics
from app.models import Stock
from app.models import Supplier


def _dead_stock_action(dead_stock_days: int, stock_value: float) -> str:
    if dead_stock_days >= 120 or stock_value >= 50000:
        return "return_to_supplier_or_stop_reorder"
    if dead_stock_days >= 60 or stock_value >= 20000:
        return "launch_promo_or_bundle"
    return "apply_discount"


def _severity(dead_stock_days: int, stock_value: float) -> str:
    if dead_stock_days >= 120 or stock_value >= 50000:
        return "critical"
    if dead_stock_days >= 60 or stock_value >= 20000:
        return "warning"
    return "info"


def flag_dead_stock(db: Session) -> dict:
    stock_subquery = (
        select(
            Stock.product_id.label("product_id"),
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
        .where(Product.is_active.is_(True))
        .order_by(Product.sku)
    )

    rows = db.execute(statement).all()
    items = []

    for row in rows:
        product = row[0]
        supplier_name = row[1]
        metrics = row[2]
        if metrics is None:
            continue

        dead_stock_days = metrics.dead_stock_days or 0
        status = metrics.status or "ok"
        available_qty = float(row.available_qty or 0)
        purchase_price = float(product.purchase_price or 0)
        stock_value = round(available_qty * purchase_price, 2)

        if status != "dead_stock" and dead_stock_days < 45:
            continue
        if available_qty <= 0:
            continue

        action = _dead_stock_action(dead_stock_days, stock_value)
        severity = _severity(dead_stock_days, stock_value)

        items.append(
            {
                "product_id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "category": product.category,
                "supplier_name": supplier_name,
                "available_qty": round(available_qty, 3),
                "purchase_price": purchase_price,
                "stock_value": stock_value,
                "days_of_stock": float(metrics.days_of_stock)
                if metrics.days_of_stock is not None
                else None,
                "last_sale_date": str(metrics.last_sale_date)
                if metrics.last_sale_date is not None
                else None,
                "dead_stock_days": dead_stock_days,
                "status": status,
                "severity": severity,
                "recommended_action": action,
                "reason": (
                    f"No significant sales for {dead_stock_days} days, stock value {stock_value}"
                ),
            }
        )

    items = sorted(
        items,
        key=lambda item: (item["dead_stock_days"], item["stock_value"]),
        reverse=True,
    )

    return {
        "summary": {
            "items_count": len(items),
            "critical_count": sum(
                1 for item in items if item["severity"] == "critical"
            ),
            "warning_count": sum(1 for item in items if item["severity"] == "warning"),
            "info_count": sum(1 for item in items if item["severity"] == "info"),
            "total_stock_value": round(sum(item["stock_value"] for item in items), 2),
        },
        "items": items,
    }

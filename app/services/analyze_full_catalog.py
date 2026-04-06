from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product
from app.models import ProductMetrics
from app.models import Stock
from app.models import Supplier


@dataclass(slots=True)
class CatalogItemAnalysis:
    product_id: str
    sku: str
    name: str
    category: str
    supplier_name: str
    available_qty: float
    total_qty: float
    reserved_qty: float
    velocity_7d: float
    days_of_stock: float | None
    reorder_point: int | None
    reorder_qty: float | None
    status: str
    priority_score: float


def _to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _priority_score(
    status: str, days_of_stock: float | None, reorder_qty: float | None
) -> float:
    base = {
        "critical": 100.0,
        "warning": 70.0,
        "ok": 30.0,
        "overstock": 20.0,
        "dead_stock": 10.0,
    }.get(status, 0.0)
    stock_component = 0.0 if days_of_stock is None else max(0.0, 30.0 - days_of_stock)
    reorder_component = 0.0 if reorder_qty is None else min(reorder_qty / 10.0, 25.0)
    return round(base + stock_component + reorder_component, 2)


def analyze_full_catalog(db: Session) -> dict:
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
        .order_by(Product.sku)
    )

    rows = db.execute(statement).all()
    items: list[CatalogItemAnalysis] = []

    for row in rows:
        product = row[0]
        supplier_name = row[1]
        metrics = row[2]
        available_qty = (
            _to_float(
                row.available_qty if row.available_qty is not None else Decimal("0")
            )
            or 0.0
        )
        total_qty = (
            _to_float(row.total_qty if row.total_qty is not None else Decimal("0"))
            or 0.0
        )
        reserved_qty = (
            _to_float(
                row.reserved_qty if row.reserved_qty is not None else Decimal("0")
            )
            or 0.0
        )
        velocity_7d = (
            _to_float(metrics.velocity_7d if metrics is not None else Decimal("0"))
            or 0.0
        )
        days_of_stock = _to_float(
            metrics.days_of_stock if metrics is not None else None
        )
        reorder_qty = _to_float(metrics.reorder_qty if metrics is not None else None)
        reorder_point = metrics.reorder_point if metrics is not None else None
        status = metrics.status if metrics is not None and metrics.status else "ok"
        priority_score = _priority_score(status, days_of_stock, reorder_qty)

        items.append(
            CatalogItemAnalysis(
                product_id=str(product.id),
                sku=product.sku,
                name=product.name,
                category=product.category or "Unknown",
                supplier_name=supplier_name or "Unknown supplier",
                available_qty=round(available_qty, 3),
                total_qty=round(total_qty, 3),
                reserved_qty=round(reserved_qty, 3),
                velocity_7d=round(velocity_7d, 3),
                days_of_stock=round(days_of_stock, 1)
                if days_of_stock is not None
                else None,
                reorder_point=reorder_point,
                reorder_qty=round(reorder_qty, 3) if reorder_qty is not None else None,
                status=status,
                priority_score=priority_score,
            )
        )

    sorted_items = sorted(items, key=lambda item: item.priority_score, reverse=True)
    grouped = {
        "critical": [item for item in sorted_items if item.status == "critical"],
        "warning": [item for item in sorted_items if item.status == "warning"],
        "ok": [item for item in sorted_items if item.status == "ok"],
    }

    return {
        "summary": {
            "total_skus": len(sorted_items),
            "critical_count": len(grouped["critical"]),
            "warning_count": len(grouped["warning"]),
            "ok_count": len(grouped["ok"]),
        },
        "top_critical": [asdict(item) for item in grouped["critical"][:10]],
        "ranked_items": [asdict(item) for item in sorted_items],
        "traffic_light": {
            "red": len(grouped["critical"]),
            "yellow": len(grouped["warning"]),
            "green": len(grouped["ok"]),
        },
    }

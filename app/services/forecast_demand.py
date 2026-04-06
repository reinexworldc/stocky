from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product
from app.models import SalesHistory


@dataclass(slots=True)
class ForecastSalesWindow:
    days: int
    total_quantity: float
    avg_daily_sales: float
    total_revenue: float


def _sum_sales_for_window(
    db: Session, product_id, start_date: date
) -> tuple[float, float]:
    statement = select(
        func.coalesce(func.sum(SalesHistory.quantity_sold), 0),
        func.coalesce(func.sum(SalesHistory.revenue), 0),
    ).where(SalesHistory.product_id == product_id, SalesHistory.date >= start_date)
    quantity, revenue = db.execute(statement).one()
    return float(quantity), float(revenue)


def _build_sales_window(
    db: Session, product_id, days: int, today: date
) -> ForecastSalesWindow:
    start_date = today - timedelta(days=days - 1)
    total_quantity, total_revenue = _sum_sales_for_window(db, product_id, start_date)
    return ForecastSalesWindow(
        days=days,
        total_quantity=round(total_quantity, 3),
        avg_daily_sales=round(total_quantity / days, 3),
        total_revenue=round(total_revenue, 2),
    )


def forecast_demand(db: Session, sku: str) -> dict | None:
    product = db.scalar(select(Product).where(Product.sku == sku))
    if product is None:
        return None

    today = date.today()
    sales_7d = _build_sales_window(db, product.id, 7, today)
    sales_30d = _build_sales_window(db, product.id, 30, today)
    sales_90d = _build_sales_window(db, product.id, 90, today)

    blended_velocity = round(
        sales_7d.avg_daily_sales * 0.6 + sales_30d.avg_daily_sales * 0.4, 3
    )
    forecast_7d = round(blended_velocity * 7, 3)
    forecast_14d = round(blended_velocity * 14, 3)
    forecast_30d = round(blended_velocity * 30, 3)

    return {
        "sku": product.sku,
        "name": product.name,
        "inputs": {
            "sales_7d": asdict(sales_7d),
            "sales_30d": asdict(sales_30d),
            "sales_90d": asdict(sales_90d),
        },
        "forecast": {
            "blended_velocity": blended_velocity,
            "forecast_7d": forecast_7d,
            "forecast_14d": forecast_14d,
            "forecast_30d": forecast_30d,
        },
        "method": {
            "formula": "blended_velocity = 0.6 * avg_daily_sales_7d + 0.4 * avg_daily_sales_30d",
            "comment": "Forecast combines short-term demand dynamics with a more stable 30-day trend.",
        },
    }

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Product

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", summary="List products")
def list_products(
    db: Session = Depends(get_db),
) -> list[dict[str, str | float | bool | None]]:
    records = db.scalars(select(Product).order_by(Product.id).limit(50)).all()
    payload: list[dict[str, str | float | bool | None]] = []
    for record in records:
        selling_price = (
            float(record.selling_price) if record.selling_price is not None else None
        )
        purchase_price = (
            float(record.purchase_price) if record.purchase_price is not None else None
        )
        payload.append(
            {
                "id": str(record.id),
                "sku": record.sku,
                "name": record.name,
                "category": record.category,
                "subcategory": record.subcategory,
                "unit": record.unit,
                "selling_price": selling_price,
                "purchase_price": purchase_price,
                "is_active": record.is_active,
            }
        )
    return payload

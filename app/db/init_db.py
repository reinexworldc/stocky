from app.db.base import Base
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models import AgentLog
from app.models import Alert
from app.models import Product
from app.models import ProductMetrics
from app.models import ProductSupplier
from app.models import PurchaseOrder
from app.models import PurchaseOrderItem
from app.models import SalesHistory
from app.models import Stock
from app.models import Supplier
from app.models import Warehouse
from app.db.seed_data import reset_database
from app.db.seed_data import seed_database


def init_db() -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    with Session(engine) as session:
        has_tables = engine.dialect.has_table(session.connection(), "products")
        has_data = False

        if has_tables:
            has_data = session.scalar(select(Product.id).limit(1)) is not None

        if not has_tables:
            Base.metadata.create_all(bind=engine)

        if not has_data:
            if has_tables:
                reset_database(session)
                Base.metadata.create_all(bind=engine)

            seed_database(session)

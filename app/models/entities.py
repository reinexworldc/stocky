from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    payment_terms: Mapped[str] = mapped_column(String(100), nullable=True)
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    products: Mapped[list["Product"]] = relationship(back_populates="primary_supplier")
    product_links: Mapped[list["ProductSupplier"]] = relationship(
        back_populates="supplier"
    )
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        back_populates="supplier"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=True)
    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    supplier_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    lead_time_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("7")
    )
    min_order_qty: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    safety_stock_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("7")
    )
    max_stock_qty: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    primary_supplier: Mapped["Supplier"] = relationship(
        back_populates="products"
    )
    supplier_links: Mapped[list["ProductSupplier"]] = relationship(
        back_populates="product"
    )
    stocks: Mapped[list["Stock"]] = relationship(back_populates="product")
    sales_history: Mapped[list["SalesHistory"]] = relationship(back_populates="product")
    metrics: Mapped["ProductMetrics"] = relationship(
        back_populates="product", uselist=False
    )
    alerts: Mapped[list["Alert"]] = relationship(back_populates="product")
    purchase_order_items: Mapped[list["PurchaseOrderItem"]] = relationship(
        back_populates="product"
    )


class ProductSupplier(Base):
    __tablename__ = "product_suppliers"
    __table_args__ = (
        UniqueConstraint("product_id", "supplier_id", name="uq_product_supplier"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    supplier_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=True)
    min_order_qty: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="supplier_links")
    supplier: Mapped["Supplier"] = relationship(back_populates="product_links")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    stocks: Mapped[list["Stock"]] = relationship(back_populates="warehouse")


class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "warehouse_id", name="uq_stock_product_warehouse"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, server_default=text("0")
    )
    reserved_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, server_default=text("0")
    )
    available_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        Computed("quantity - reserved_qty", persisted=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="stocks")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="stocks")


class SalesHistory(Base):
    __tablename__ = "sales_history"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity_sold: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=True
    )
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    order_source: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="sales_history")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    supplier_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'draft'")
    )
    created_by: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'agent'")
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    expected_delivery_date: Mapped[date] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    supplier: Mapped["Supplier"] = relationship(
        back_populates="purchase_orders"
    )
    items: Mapped[list["PurchaseOrderItem"]] = relationship(back_populates="order")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=True
    )
    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    order: Mapped["PurchaseOrder"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(
        back_populates="purchase_order_items"
    )


class ProductMetrics(Base):
    __tablename__ = "product_metrics"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, unique=True
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    velocity_7d: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=True
    )
    velocity_30d: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=True
    )
    velocity_90d: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=True
    )
    days_of_stock: Mapped[Decimal] = mapped_column(
        Numeric(10, 1), nullable=True
    )
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=True)
    reorder_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    last_sale_date: Mapped[date] = mapped_column(Date, nullable=True)
    dead_stock_days: Mapped[int] = mapped_column(Integer, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="metrics")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="alerts")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    tool_called: Mapped[str] = mapped_column(String(100), nullable=True)
    input: Mapped[dict] = mapped_column(JSONB, nullable=True)
    output: Mapped[dict] = mapped_column(JSONB, nullable=True)
    reasoning: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

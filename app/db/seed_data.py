from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

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


TODAY = date(2026, 4, 4)
NOW = datetime(2026, 4, 4, 12, 0, 0)

SUPPLIER_DATA = [
    {
        "name": "FreshMarket LLC",
        "contact_name": "Elena Smirnova",
        "phone": "+7-495-100-10-01",
        "email": "orders@freshmarket.example",
        "payment_terms": "net 30",
        "min_order_amount": Decimal("15000.00"),
    },
    {
        "name": "Nord Dairy",
        "contact_name": "Ivan Petrov",
        "phone": "+7-812-220-18-40",
        "email": "supply@nordmilk.example",
        "payment_terms": "prepaid",
        "min_order_amount": Decimal("12000.00"),
    },
    {
        "name": "Volga Beverages",
        "contact_name": "Olga Romanova",
        "phone": "+7-831-333-20-11",
        "email": "b2b@volgadrinks.example",
        "payment_terms": "net 30",
        "min_order_amount": Decimal("18000.00"),
    },
    {
        "name": "Prime Home Care",
        "contact_name": "Maxim Sokolov",
        "phone": "+7-343-410-08-77",
        "email": "trade@primehome.example",
        "payment_terms": "net 60",
        "min_order_amount": Decimal("20000.00"),
    },
    {
        "name": "Urban Snacks Factory",
        "contact_name": "Natalia Volkova",
        "phone": "+7-499-555-77-12",
        "email": "partners@urbansnacks.example",
        "payment_terms": "prepaid",
        "min_order_amount": Decimal("10000.00"),
    },
    {
        "name": "CleanLine Household",
        "contact_name": "Darya Kuznetsova",
        "phone": "+7-381-222-90-44",
        "email": "orders@cleanline.example",
        "payment_terms": "net 30",
        "min_order_amount": Decimal("16000.00"),
    },
]

WAREHOUSE_DATA = [
    {"name": "Moscow Central DC", "address": "19 Kashirskoye Hwy, Moscow"},
    {"name": "Saint Petersburg Hub", "address": "62 Sofiyskaya St, Saint Petersburg"},
    {"name": "Kazan Reserve Warehouse", "address": "11 Tekhnicheskaya St, Kazan"},
]

PRODUCT_DATA = [
    (
        "FRT-APL-001",
        "Gala Apples",
        "Fresh Produce",
        "Fruits",
        "kg",
        "72.00",
        "119.00",
        0,
        3,
        20,
        4,
        600,
    ),
    (
        "FRT-BAN-002",
        "Bananas",
        "Fresh Produce",
        "Fruits",
        "kg",
        "68.00",
        "112.00",
        0,
        4,
        18,
        4,
        550,
    ),
    (
        "FRT-ORG-003",
        "Oranges",
        "Fresh Produce",
        "Fruits",
        "kg",
        "75.00",
        "125.00",
        0,
        5,
        15,
        5,
        520,
    ),
    (
        "FRT-LEM-004",
        "Lemons",
        "Fresh Produce",
        "Fruits",
        "kg",
        "81.00",
        "139.00",
        0,
        5,
        12,
        5,
        420,
    ),
    (
        "VEG-TOM-005",
        "Roma Tomatoes",
        "Fresh Produce",
        "Vegetables",
        "kg",
        "96.00",
        "159.00",
        0,
        2,
        14,
        3,
        380,
    ),
    (
        "VEG-CUC-006",
        "Short Cucumbers",
        "Fresh Produce",
        "Vegetables",
        "kg",
        "88.00",
        "149.00",
        0,
        2,
        16,
        3,
        360,
    ),
    (
        "VEG-POT-007",
        "Washed Potatoes",
        "Fresh Produce",
        "Vegetables",
        "kg",
        "34.00",
        "59.00",
        0,
        4,
        30,
        7,
        1200,
    ),
    (
        "VEG-CAR-008",
        "Carrots",
        "Fresh Produce",
        "Vegetables",
        "kg",
        "39.00",
        "69.00",
        0,
        4,
        26,
        7,
        980,
    ),
    (
        "DRY-RIC-009",
        "Basmati Rice 900g",
        "Groceries",
        "Grains",
        "pcs",
        "82.00",
        "139.00",
        4,
        10,
        24,
        10,
        800,
    ),
    (
        "DRY-PAS-010",
        "Penne Pasta 450g",
        "Groceries",
        "Pasta",
        "pcs",
        "41.00",
        "79.00",
        4,
        9,
        30,
        10,
        900,
    ),
    (
        "DRY-OAT-011",
        "Oat Flakes 800g",
        "Groceries",
        "Breakfast",
        "pcs",
        "55.00",
        "97.00",
        4,
        7,
        20,
        8,
        640,
    ),
    (
        "DRY-BCK-012",
        "Buckwheat 900g",
        "Groceries",
        "Grains",
        "pcs",
        "47.00",
        "84.00",
        4,
        8,
        18,
        8,
        700,
    ),
    (
        "OIL-SUN-013",
        "Sunflower Oil 1L",
        "Groceries",
        "Oil",
        "L",
        "88.00",
        "149.00",
        4,
        11,
        12,
        10,
        560,
    ),
    (
        "CAN-BEA-014",
        "Red Beans 400g",
        "Groceries",
        "Canned Goods",
        "pcs",
        "46.00",
        "83.00",
        4,
        8,
        24,
        10,
        610,
    ),
    (
        "CAN-CRN-015",
        "Sweet Corn 340g",
        "Groceries",
        "Canned Goods",
        "pcs",
        "43.00",
        "78.00",
        4,
        8,
        24,
        10,
        620,
    ),
    (
        "SNA-CHP-016",
        "Salted Potato Chips 150g",
        "Snacks",
        "Chips",
        "pcs",
        "39.00",
        "89.00",
        4,
        6,
        24,
        7,
        700,
    ),
    (
        "SNA-NUT-017",
        "Almond Mix 120g",
        "Snacks",
        "Nuts",
        "pcs",
        "92.00",
        "179.00",
        4,
        7,
        16,
        8,
        420,
    ),
    (
        "SNA-CRA-018",
        "Whole Grain Crackers 200g",
        "Snacks",
        "Crackers",
        "pcs",
        "31.00",
        "67.00",
        4,
        6,
        20,
        7,
        550,
    ),
    (
        "SNA-COK-019",
        "Chocolate Filled Cookies 220g",
        "Snacks",
        "Cookies",
        "pcs",
        "45.00",
        "96.00",
        4,
        7,
        18,
        8,
        580,
    ),
    (
        "SNA-BAR-020",
        "Hazelnut Protein Bar 60g",
        "Snacks",
        "Healthy Snacks",
        "pcs",
        "52.00",
        "109.00",
        4,
        6,
        30,
        10,
        480,
    ),
    (
        "DRK-WAT-021",
        "Still Drinking Water 1.5L",
        "Beverages",
        "Water",
        "L",
        "19.00",
        "39.00",
        2,
        5,
        60,
        7,
        2000,
    ),
    (
        "DRK-SPK-022",
        "Sparkling Water 1.5L",
        "Beverages",
        "Water",
        "L",
        "21.00",
        "42.00",
        2,
        5,
        54,
        7,
        1800,
    ),
    (
        "DRK-COL-023",
        "Classic Cola 1L",
        "Beverages",
        "Soda",
        "L",
        "44.00",
        "85.00",
        2,
        6,
        36,
        8,
        1200,
    ),
    (
        "DRK-LEM-024",
        "Lemonade 1L",
        "Beverages",
        "Soda",
        "L",
        "42.00",
        "82.00",
        2,
        6,
        32,
        8,
        1100,
    ),
    (
        "DRK-JUI-025",
        "Orange Juice 1L",
        "Beverages",
        "Juices",
        "L",
        "64.00",
        "118.00",
        2,
        6,
        20,
        8,
        760,
    ),
    (
        "DRK-APP-026",
        "Apple Juice 1L",
        "Beverages",
        "Juices",
        "L",
        "61.00",
        "113.00",
        2,
        6,
        20,
        8,
        760,
    ),
    (
        "DRK-ICE-027",
        "Peach Iced Tea 1L",
        "Beverages",
        "Iced Tea",
        "L",
        "39.00",
        "79.00",
        2,
        6,
        28,
        8,
        820,
    ),
    (
        "DRK-ENG-028",
        "Energy Drink 0.45L",
        "Beverages",
        "Energy Drinks",
        "pcs",
        "55.00",
        "119.00",
        2,
        5,
        24,
        7,
        640,
    ),
    (
        "DAI-MLK-029",
        "Milk 3.2% 1L",
        "Dairy",
        "Milk",
        "L",
        "56.00",
        "94.00",
        1,
        2,
        24,
        3,
        900,
    ),
    (
        "DAI-KFR-030",
        "Kefir 930ml",
        "Dairy",
        "Fermented Dairy",
        "L",
        "49.00",
        "88.00",
        1,
        2,
        20,
        3,
        820,
    ),
    (
        "DAI-YOG-031",
        "Plain Greek Yogurt 140g",
        "Dairy",
        "Yogurts",
        "pcs",
        "28.00",
        "59.00",
        1,
        2,
        36,
        3,
        760,
    ),
    (
        "DAI-CHS-032",
        "Semi-Hard Cheese 200g",
        "Dairy",
        "Cheeses",
        "pcs",
        "118.00",
        "198.00",
        1,
        4,
        16,
        5,
        430,
    ),
    (
        "DAI-BTR-033",
        "Butter 180g",
        "Dairy",
        "Oil",
        "pcs",
        "95.00",
        "169.00",
        1,
        4,
        20,
        5,
        410,
    ),
    (
        "DAI-SCM-034",
        "Sour Cream 20% 300g",
        "Dairy",
        "Sour Cream",
        "pcs",
        "41.00",
        "79.00",
        1,
        2,
        24,
        3,
        680,
    ),
    (
        "CLN-GEL-035",
        "Laundry Gel 2L",
        "Household",
        "Laundry",
        "L",
        "174.00",
        "289.00",
        3,
        9,
        8,
        12,
        260,
    ),
    (
        "CLN-PWD-036",
        "Color Laundry Powder 3kg",
        "Household",
        "Laundry",
        "kg",
        "248.00",
        "399.00",
        3,
        9,
        6,
        12,
        220,
    ),
    (
        "CLN-DIS-037",
        "Citrus Dish Soap 500ml",
        "Household",
        "Kitchen",
        "L",
        "57.00",
        "109.00",
        3,
        7,
        24,
        9,
        620,
    ),
    (
        "CLN-MLT-038",
        "All-Purpose Cleaner 750ml",
        "Household",
        "Surface Care",
        "L",
        "66.00",
        "124.00",
        3,
        7,
        18,
        9,
        540,
    ),
    (
        "CLN-SOAP-039",
        "Aloe Liquid Soap 500ml",
        "Household",
        "Personal Care",
        "L",
        "48.00",
        "92.00",
        3,
        7,
        20,
        8,
        600,
    ),
    (
        "CLN-TIS-040",
        "Paper Towels 2 Rolls",
        "Household",
        "Paper Products",
        "pcs",
        "52.00",
        "99.00",
        5,
        8,
        30,
        10,
        760,
    ),
    (
        "CLN-TLT-041",
        "Soft Toilet Paper 8 Rolls",
        "Household",
        "Paper Products",
        "pcs",
        "118.00",
        "199.00",
        5,
        8,
        18,
        10,
        520,
    ),
    (
        "CLN-BAG-042",
        "Trash Bags 60L 20 pcs",
        "Household",
        "Storage",
        "pcs",
        "36.00",
        "74.00",
        5,
        6,
        26,
        9,
        640,
    ),
    (
        "BAK-BRD-043",
        "Sliced Wheat Bread 500g",
        "Bakery",
        "Bread",
        "pcs",
        "29.00",
        "54.00",
        0,
        1,
        40,
        2,
        480,
    ),
    (
        "BAK-BUN-044",
        "Burger Buns 4 pcs",
        "Bakery",
        "Buns",
        "pcs",
        "38.00",
        "72.00",
        0,
        1,
        24,
        2,
        360,
    ),
    (
        "BAK-CRS-045",
        "Butter Croissant 70g",
        "Bakery",
        "Pastry",
        "pcs",
        "21.00",
        "45.00",
        0,
        1,
        50,
        2,
        340,
    ),
    (
        "FRZ-BER-046",
        "Frozen Berry Mix 400g",
        "Frozen",
        "Berries",
        "pcs",
        "98.00",
        "169.00",
        0,
        6,
        18,
        12,
        420,
    ),
    (
        "FRZ-VEG-047",
        "Frozen Vegetable Mix 400g",
        "Frozen",
        "Vegetables",
        "pcs",
        "76.00",
        "139.00",
        0,
        6,
        20,
        12,
        450,
    ),
    (
        "PET-DRY-048",
        "Chicken Cat Food 1.5kg",
        "Pet Supplies",
        "Cat Food",
        "kg",
        "214.00",
        "349.00",
        5,
        10,
        8,
        14,
        240,
    ),
    (
        "PET-WET-049",
        "Beef Dog Food 85g",
        "Pet Supplies",
        "Dog Food",
        "pcs",
        "24.00",
        "49.00",
        5,
        10,
        48,
        14,
        1100,
    ),
    (
        "PET-LIT-050",
        "Clumping Cat Litter 5kg",
        "Pet Supplies",
        "Hygiene",
        "kg",
        "168.00",
        "289.00",
        5,
        12,
        10,
        15,
        260,
    ),
]


def reset_database(session: Session) -> None:
    table_names = [
        "agent_logs",
        "alerts",
        "product_metrics",
        "purchase_order_items",
        "purchase_orders",
        "sales_history",
        "stock",
        "product_suppliers",
        "products",
        "warehouses",
        "suppliers",
        "stocky",
    ]
    session.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    for table_name in table_names:
        session.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
    session.commit()


def seed_database(session: Session) -> None:
    if session.query(Product).first() is not None:
        return

    suppliers = [
        Supplier(created_at=NOW, is_active=True, **payload) for payload in SUPPLIER_DATA
    ]
    warehouses = [Warehouse(is_active=True, **payload) for payload in WAREHOUSE_DATA]
    session.add_all(suppliers + warehouses)
    session.flush()

    products: list[Product] = []
    product_suppliers: list[ProductSupplier] = []
    stock_rows: list[Stock] = []
    sales_rows: list[SalesHistory] = []
    metric_rows: list[ProductMetrics] = []
    alert_rows: list[Alert] = []

    sources = ["website", "wildberries", "ozon", "wholesale"]
    statuses = ["ok", "ok", "warning", "critical", "overstock", "dead_stock"]

    for index, item in enumerate(PRODUCT_DATA):
        (
            sku,
            name,
            category,
            subcategory,
            unit,
            purchase_price,
            selling_price,
            supplier_idx,
            lead_time,
            min_qty,
            safety_days,
            max_qty,
        ) = item
        supplier = suppliers[supplier_idx]
        product = Product(
            sku=sku,
            name=name,
            category=category,
            subcategory=subcategory,
            unit=unit,
            purchase_price=Decimal(purchase_price),
            selling_price=Decimal(selling_price),
            primary_supplier=supplier,
            lead_time_days=lead_time,
            min_order_qty=min_qty,
            safety_stock_days=safety_days,
            max_stock_qty=max_qty,
            is_active=True,
            created_at=NOW - timedelta(days=index % 30),
        )
        products.append(product)
        session.add(product)
        session.flush()

        alt_supplier = suppliers[(supplier_idx + 1) % len(suppliers)]
        product_suppliers.extend(
            [
                ProductSupplier(
                    product=product,
                    supplier=supplier,
                    purchase_price=Decimal(purchase_price),
                    lead_time_days=lead_time,
                    min_order_qty=min_qty,
                    is_primary=True,
                    updated_at=NOW,
                ),
                ProductSupplier(
                    product=product,
                    supplier=alt_supplier,
                    purchase_price=(Decimal(purchase_price) * Decimal("1.06")).quantize(
                        Decimal("0.01")
                    ),
                    lead_time_days=lead_time + 2,
                    min_order_qty=max(1, min_qty // 2),
                    is_primary=False,
                    updated_at=NOW - timedelta(days=2),
                ),
            ]
        )

        total_quantity = Decimal(str(40 + (index % 10) * 18))
        for warehouse_index, warehouse in enumerate(warehouses):
            warehouse_quantity = (
                total_quantity * Decimal(str(0.5 - warehouse_index * 0.1))
            ).quantize(Decimal("0.001"))
            if warehouse_quantity <= 0:
                warehouse_quantity = Decimal("5.000")
            reserved = (warehouse_quantity * Decimal("0.12")).quantize(Decimal("0.001"))
            stock_rows.append(
                Stock(
                    product=product,
                    warehouse=warehouse,
                    quantity=warehouse_quantity,
                    reserved_qty=reserved,
                    updated_at=NOW - timedelta(hours=warehouse_index * 5 + index % 7),
                )
            )

        sale_days = 12 if index % 9 != 0 else 2
        last_sale_date = TODAY - timedelta(
            days=(index % 17) if index % 9 != 0 else 45 + index % 20
        )
        for sale_index in range(sale_days):
            sale_date = last_sale_date - timedelta(days=sale_index * 3)
            quantity_sold = Decimal(
                str(round(1.5 + ((index + sale_index) % 5) * 0.75, 3))
            )
            revenue = (quantity_sold * Decimal(selling_price)).quantize(Decimal("0.01"))
            sales_rows.append(
                SalesHistory(
                    product=product,
                    date=sale_date,
                    quantity_sold=quantity_sold,
                    revenue=revenue,
                    order_source=sources[(index + sale_index) % len(sources)],
                    created_at=datetime.combine(sale_date, datetime.min.time()),
                )
            )

        velocity_7d = Decimal(str(round(0.4 + (index % 6) * 0.35, 3)))
        velocity_30d = Decimal(str(round(0.6 + (index % 7) * 0.28, 3)))
        velocity_90d = Decimal(str(round(0.7 + (index % 8) * 0.22, 3)))
        stock_sum = sum((row.quantity - row.reserved_qty) for row in stock_rows[-3:])
        days_of_stock = (
            None
            if velocity_7d == 0
            else (stock_sum / velocity_7d).quantize(Decimal("0.1"))
        )
        reorder_point = lead_time + safety_days
        reorder_qty = Decimal(str(max_qty)) - stock_sum
        if reorder_qty < 0:
            reorder_qty = Decimal("0.000")
        status = statuses[index % len(statuses)]
        dead_stock_days = (TODAY - last_sale_date).days
        metric_rows.append(
            ProductMetrics(
                product=product,
                calculated_at=NOW,
                velocity_7d=velocity_7d,
                velocity_30d=velocity_30d,
                velocity_90d=velocity_90d,
                days_of_stock=days_of_stock,
                reorder_point=reorder_point,
                reorder_qty=reorder_qty.quantize(Decimal("0.001")),
                status=status,
                last_sale_date=last_sale_date,
                dead_stock_days=dead_stock_days,
            )
        )

        if status in {"critical", "warning", "dead_stock", "overstock"}:
            message_map = {
                "critical": f"Product {name} will run out in less than three days at the current sales rate.",
                "warning": f"Product {name} has dropped below the reorder point and needs replenishment.",
                "dead_stock": f"Product {name} has had no sales for a long time and needs to be reviewed.",
                "overstock": f"Product {name} has excess stock across active warehouses.",
            }
            severity_map = {
                "critical": "critical",
                "warning": "warning",
                "dead_stock": "info",
                "overstock": "warning",
            }
            alert_type_map = {
                "critical": "stockout_risk",
                "warning": "stockout_risk",
                "dead_stock": "dead_stock",
                "overstock": "overstock",
            }
            alert_rows.append(
                Alert(
                    product=product,
                    type=alert_type_map[status],
                    severity=severity_map[status],
                    message=message_map[status],
                    is_read=index % 4 == 0,
                    triggered_at=NOW - timedelta(hours=index),
                )
            )

    session.add_all(product_suppliers)
    session.add_all(stock_rows)
    session.add_all(sales_rows)
    session.add_all(metric_rows)
    session.add_all(alert_rows)
    session.flush()

    purchase_orders: list[PurchaseOrder] = []
    purchase_items: list[PurchaseOrderItem] = []
    order_statuses = ["draft", "confirmed", "shipped", "received", "cancelled"]
    for order_index in range(8):
        supplier = suppliers[order_index % len(suppliers)]
        order_products = products[order_index * 3 : order_index * 3 + 3]
        if len(order_products) < 3:
            order_products = products[-3:]
        order = PurchaseOrder(
            supplier=supplier,
            status=order_statuses[order_index % len(order_statuses)],
            created_by="agent" if order_index % 2 == 0 else "human",
            total_amount=Decimal("0.00"),
            expected_delivery_date=TODAY + timedelta(days=5 + order_index * 2),
            notes=f"Scheduled replenishment order #{order_index + 1}",
            created_at=NOW - timedelta(days=order_index * 2),
        )
        purchase_orders.append(order)
        session.add(order)
        session.flush()

        total_amount = Decimal("0.00")
        for item_index, product in enumerate(order_products):
            qty = Decimal(str(product.min_order_qty * (item_index + 2)))
            line_amount = (qty * product.purchase_price).quantize(Decimal("0.01"))
            total_amount += line_amount
            purchase_items.append(
                PurchaseOrderItem(
                    order=order,
                    product=product,
                    quantity_ordered=qty.quantize(Decimal("0.001")),
                    purchase_price=product.purchase_price,
                    quantity_received=(qty * Decimal("0.5")).quantize(Decimal("0.001"))
                    if order.status == "received"
                    else Decimal("0.000"),
                    created_at=NOW - timedelta(days=order_index * 2),
                )
            )
        order.total_amount = total_amount

    session.add_all(purchase_items)

    logs = [
        AgentLog(
            session_id=uuid4(),
            tool_called="inventory_recalc",
            input={"scope": "all_products", "batch": 50},
            output={"updated_metrics": 50, "alerts_created": len(alert_rows)},
            reasoning="Nightly refresh recalculated velocities, reorder points, and stock health statuses.",
            created_at=NOW - timedelta(hours=4),
        ),
        AgentLog(
            session_id=uuid4(),
            tool_called="supplier_order_planner",
            input={"mode": "auto", "suppliers_considered": len(suppliers)},
            output={"purchase_orders_created": len(purchase_orders)},
            reasoning="The planner grouped low-stock SKUs by primary supplier to reduce split shipments.",
            created_at=NOW - timedelta(hours=2),
        ),
    ]
    session.add_all(logs)
    session.commit()

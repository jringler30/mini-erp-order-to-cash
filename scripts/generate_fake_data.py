# scripts/generate_fake_data.py
# Generates realistic fake ERP data and returns it as lists of dicts.
# Called by load_data.py to populate erp.db.

from faker import Faker
import random
from datetime import date, timedelta

fake = Faker()
random.seed(42)
Faker.seed(42)

# ─────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────

def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ─────────────────────────────────────────
# CUSTOMERS  (200 records)
# ─────────────────────────────────────────

REGIONS    = ["North", "South", "East", "West"]
INDUSTRIES = ["Manufacturing", "Retail", "Healthcare", "Technology", "Finance", "Logistics"]

def generate_customers(n=200):
    customers = []
    emails_used = set()
    for i in range(1, n + 1):
        email = fake.unique.company_email()
        customers.append({
            "customer_id":    i,
            "customer_name":  fake.company(),
            "customer_email": email,
            "region":         random.choice(REGIONS),
            "industry":       random.choice(INDUSTRIES),
            "created_date":   str(random_date(date(2021, 1, 1), date(2023, 6, 1))),
        })
    return customers


# ─────────────────────────────────────────
# PRODUCTS  (40 records)
# ─────────────────────────────────────────

PRODUCT_CATALOG = [
    ("Widget A",        "Hardware",   8.50,   19.99),
    ("Widget B",        "Hardware",   12.00,  29.99),
    ("Widget C",        "Hardware",   5.00,   12.49),
    ("Bolt Pack 100",   "Hardware",   2.00,   5.99),
    ("Steel Rod 1m",    "Hardware",   15.00,  34.99),
    ("Copper Wire 5m",  "Hardware",   7.50,   18.99),
    ("Circuit Board X", "Electronics", 22.00, 54.99),
    ("Circuit Board Y", "Electronics", 18.00, 44.99),
    ("Power Supply 12V","Electronics", 30.00, 69.99),
    ("USB Hub 4-Port",  "Electronics", 10.00, 24.99),
    ("Sensor Module A", "Electronics", 25.00, 59.99),
    ("LED Strip 1m",    "Electronics",  4.00, 11.99),
    ("Safety Gloves L", "Safety",       3.50,  8.99),
    ("Safety Gloves M", "Safety",       3.50,  8.99),
    ("Hard Hat Yellow", "Safety",       8.00, 19.99),
    ("Hard Hat White",  "Safety",       8.00, 19.99),
    ("Safety Vest M",   "Safety",       5.00, 12.99),
    ("Safety Vest L",   "Safety",       5.00, 12.99),
    ("Drill Bit Set",   "Tools",       14.00, 34.99),
    ("Wrench Set 10pc", "Tools",       20.00, 49.99),
    ("Screwdriver Set", "Tools",        9.00, 22.99),
    ("Tape Measure 5m", "Tools",        4.50, 10.99),
    ("Level 60cm",      "Tools",        7.00, 17.99),
    ("Hammer 500g",     "Tools",        6.00, 14.99),
    ("PVC Pipe 1m",     "Materials",    3.00,  7.49),
    ("PVC Elbow 90deg", "Materials",    1.00,  2.99),
    ("Concrete Mix 5kg","Materials",    4.00,  9.99),
    ("Plywood Sheet",   "Materials",   18.00, 42.99),
    ("Insulation Roll", "Materials",   22.00, 54.99),
    ("Caulk Tube",      "Materials",    2.50,  6.49),
    ("Office Chair",    "Furniture",   85.00, 199.99),
    ("Standing Desk",   "Furniture",  150.00, 349.99),
    ("Monitor Stand",   "Furniture",   25.00,  59.99),
    ("Filing Cabinet",  "Furniture",   60.00, 139.99),
    ("Whiteboard 90cm", "Furniture",   35.00,  84.99),
    ("Label Maker",     "Office",       18.00,  42.99),
    ("Stapler Pro",     "Office",        5.00,  12.99),
    ("Binder A4 50mm",  "Office",        2.00,   4.99),
    ("Printer Paper A4","Office",        8.00,  18.99),
    ("Ink Cartridge BK","Office",       12.00,  29.99),
]

def generate_products():
    products = []
    for i, (name, category, cost, price) in enumerate(PRODUCT_CATALOG, start=1):
        sku = f"SKU-{category[:3].upper()}-{i:03d}"
        products.append({
            "product_id":   i,
            "sku":          sku,
            "product_name": name,
            "category":     category,
            "unit_cost":    cost,
            "unit_price":   price,
            "active_flag":  1,
        })
    return products


# ─────────────────────────────────────────
# WAREHOUSES  (3 records)
# ─────────────────────────────────────────

def generate_warehouses():
    return [
        {"warehouse_id": 1, "warehouse_name": "East Coast Hub",   "city": "Newark",      "state": "NJ"},
        {"warehouse_id": 2, "warehouse_name": "Midwest Center",   "city": "Columbus",    "state": "OH"},
        {"warehouse_id": 3, "warehouse_name": "West Coast Depot", "city": "Los Angeles", "state": "CA"},
    ]


# ─────────────────────────────────────────
# INVENTORY  (product × warehouse)
# ─────────────────────────────────────────

def generate_inventory(products, warehouses):
    inventory = []
    inv_id = 1
    for warehouse in warehouses:
        for product in products:
            qty = random.randint(20, 300)
            reorder = random.randint(10, 40)
            # Randomly make ~15% of products low stock to trigger dashboard alerts
            if random.random() < 0.15:
                qty = random.randint(0, reorder - 1)
            inventory.append({
                "inventory_id":     inv_id,
                "warehouse_id":     warehouse["warehouse_id"],
                "product_id":       product["product_id"],
                "quantity_on_hand": qty,
                "reorder_point":    reorder,
                "last_updated":     str(date(2024, 1, 1)),
            })
            inv_id += 1
    return inventory


# ─────────────────────────────────────────
# SALES ORDERS + ORDER ITEMS  (1,000 orders)
# ─────────────────────────────────────────

STATUSES = ["Pending", "Shipped", "Invoiced", "Paid", "Paid", "Paid"]  # weighted toward Paid

def generate_orders_and_items(customers, products, n=1000):
    orders = []
    items  = []
    item_id = 1

    # Some customers order more than others (realistic)
    customer_weights = [random.randint(1, 10) for _ in customers]

    for order_id in range(1, n + 1):
        customer = random.choices(customers, weights=customer_weights, k=1)[0]
        order_date = random_date(date(2023, 1, 1), date(2024, 12, 31))
        status = random.choice(STATUSES)

        requested_ship = order_date + timedelta(days=random.randint(3, 10))
        actual_ship    = None
        if status != "Pending":
            delay = random.randint(-2, 7)  # sometimes early, sometimes late
            actual_ship = requested_ship + timedelta(days=delay)

        # Generate 1–5 line items per order
        num_items = random.randint(1, 5)
        order_products = random.sample(products, k=min(num_items, len(products)))
        total_amount = 0.0

        for product in order_products:
            qty        = random.randint(1, 20)
            unit_price = product["unit_price"]
            line_total = round(qty * unit_price, 2)
            total_amount += line_total
            items.append({
                "order_item_id": item_id,
                "order_id":      order_id,
                "product_id":    product["product_id"],
                "quantity":      qty,
                "unit_price":    unit_price,
                "line_total":    line_total,
            })
            item_id += 1

        orders.append({
            "order_id":            order_id,
            "customer_id":         customer["customer_id"],
            "order_date":          str(order_date),
            "order_status":        status,
            "requested_ship_date": str(requested_ship),
            "actual_ship_date":    str(actual_ship) if actual_ship else None,
            "total_amount":        round(total_amount, 2),
        })

    return orders, items


# ─────────────────────────────────────────
# SHIPMENTS
# ─────────────────────────────────────────

def generate_shipments(orders, warehouses):
    shipments = []
    shipment_id = 1
    for order in orders:
        if order["order_status"] in ("Shipped", "Invoiced", "Paid"):
            ship_date     = order["actual_ship_date"]
            delivery_date = str(
                date.fromisoformat(ship_date) + timedelta(days=random.randint(1, 7))
            )
            status = "Delivered" if order["order_status"] in ("Invoiced", "Paid") else "Shipped"
            shipments.append({
                "shipment_id":     shipment_id,
                "order_id":        order["order_id"],
                "warehouse_id":    random.choice(warehouses)["warehouse_id"],
                "shipment_date":   ship_date,
                "delivery_date":   delivery_date,
                "shipment_status": status,
            })
            shipment_id += 1
    return shipments


# ─────────────────────────────────────────
# INVOICES
# ─────────────────────────────────────────

def generate_invoices(orders):
    invoices = []
    invoice_id = 1
    for order in orders:
        if order["order_status"] in ("Invoiced", "Paid"):
            invoice_date = str(
                date.fromisoformat(order["actual_ship_date"]) + timedelta(days=1)
            )
            due_date = str(
                date.fromisoformat(invoice_date) + timedelta(days=30)
            )
            # Some invoices remain unpaid or overdue for dashboard realism
            if order["order_status"] == "Paid":
                status = "Paid"
            elif date.fromisoformat(due_date) < date(2025, 1, 1):
                status = "Overdue"
            else:
                status = "Unpaid"

            invoices.append({
                "invoice_id":     invoice_id,
                "order_id":       order["order_id"],
                "invoice_date":   invoice_date,
                "due_date":       due_date,
                "invoice_amount": order["total_amount"],
                "invoice_status": status,
            })
            invoice_id += 1
    return invoices


# ─────────────────────────────────────────
# PAYMENTS
# ─────────────────────────────────────────

def generate_payments(invoices):
    payments = []
    payment_id = 1
    methods = ["Credit Card", "Bank Transfer", "Check", "Cash"]
    for invoice in invoices:
        if invoice["invoice_status"] == "Paid":
            pay_date = str(
                date.fromisoformat(invoice["invoice_date"]) + timedelta(days=random.randint(1, 28))
            )
            payments.append({
                "payment_id":     payment_id,
                "invoice_id":     invoice["invoice_id"],
                "payment_date":   pay_date,
                "payment_amount": invoice["invoice_amount"],
                "payment_method": random.choice(methods),
            })
            payment_id += 1
    return payments


# ─────────────────────────────────────────
# MAIN — generate everything
# ─────────────────────────────────────────

def generate_all():
    print("Generating customers...")
    customers  = generate_customers()

    print("Generating products...")
    products   = generate_products()

    print("Generating warehouses...")
    warehouses = generate_warehouses()

    print("Generating inventory...")
    inventory  = generate_inventory(products, warehouses)

    print("Generating sales orders and order items...")
    orders, order_items = generate_orders_and_items(customers, products)

    print("Generating shipments...")
    shipments  = generate_shipments(orders, warehouses)

    print("Generating invoices...")
    invoices   = generate_invoices(orders)

    print("Generating payments...")
    payments   = generate_payments(invoices)

    print(f"\nSummary:")
    print(f"  Customers:    {len(customers)}")
    print(f"  Products:     {len(products)}")
    print(f"  Warehouses:   {len(warehouses)}")
    print(f"  Inventory:    {len(inventory)}")
    print(f"  Orders:       {len(orders)}")
    print(f"  Order Items:  {len(order_items)}")
    print(f"  Shipments:    {len(shipments)}")
    print(f"  Invoices:     {len(invoices)}")
    print(f"  Payments:     {len(payments)}")

    return {
        "customers":   customers,
        "products":    products,
        "warehouses":  warehouses,
        "inventory":   inventory,
        "orders":      orders,
        "order_items": order_items,
        "shipments":   shipments,
        "invoices":    invoices,
        "payments":    payments,
    }


if __name__ == "__main__":
    generate_all()

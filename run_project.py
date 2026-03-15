#!/usr/bin/env python3
"""
run_project.py
──────────────
Master orchestration script for the Mini ERP Order-to-Cash system.

Run this once from the project root to build the full data pipeline:

    python run_project.py

What it does, in order:
  Step 1 — Create OLTP tables from sql/schema.sql
  Step 2 — Generate synthetic ERP data (customers, orders, shipments, etc.)
  Step 3 — Load that data into the OLTP tables
  Step 4 — Build the star schema analytics tables from sql/star_schema.sql
  Step 5 — Populate dimension tables (dim_customer, dim_product, etc.)
  Step 6 — Populate fact tables (fact_sales, fact_shipments, fact_payments)

After this completes, launch the dashboard with:
    streamlit run app/streamlit_app.py
"""

import sys
import sqlite3
from pathlib import Path

# ── Project root and sub-directory paths ──────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH  = BASE_DIR / "data" / "erp.db"

# Add scripts/ and etl/ to sys.path so we can import their modules.
# This mirrors how the individual scripts resolve their own imports.
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(BASE_DIR / "etl"))


# ── Step 1: Create transactional (OLTP) tables ────────────────────────────────

def step1_create_oltp_tables():
    """Read sql/schema.sql and create all 9 OLTP tables in erp.db."""
    print("\n── Step 1: Creating OLTP tables ────────────────────────────────────")

    schema_path = BASE_DIR / "sql" / "schema.sql"
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print("  OLTP tables created: customers, products, warehouses, inventory,")
        print("  sales_orders, sales_order_items, shipments, invoices, payments")
    finally:
        conn.close()


# ── Step 2 + 3: Generate fake data and load it ────────────────────────────────

def step2_load_raw_erp_data():
    """Generate synthetic ERP data and insert it into the OLTP tables.

    Uses the same logic as scripts/load_data.py but called from here so
    run_project.py is the single entry point for the whole pipeline.
    """
    print("\n── Step 2: Generating synthetic ERP data ───────────────────────────")
    from generate_fake_data import generate_all
    data = generate_all()
    print("  Data generation complete.")

    print("\n── Step 3: Loading data into OLTP tables ───────────────────────────")
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing data in reverse foreign-key order to avoid constraint errors
    print("  Clearing existing data...")
    for table in [
        "payments", "invoices", "shipments",
        "sales_order_items", "sales_orders",
        "inventory", "products", "warehouses", "customers",
    ]:
        cursor.execute(f"DELETE FROM {table}")
    conn.commit()

    # ── Insert each table ──────────────────────────────────────────────────────
    # Each entry: (table_name, INSERT SQL, list of row tuples)

    inserts = [
        (
            "customers",
            "INSERT INTO customers VALUES (?,?,?,?,?,?)",
            [
                (d["customer_id"], d["customer_name"], d["customer_email"],
                 d["region"], d["industry"], d["created_date"])
                for d in data["customers"]
            ],
        ),
        (
            "products",
            "INSERT INTO products VALUES (?,?,?,?,?,?,?)",
            [
                (d["product_id"], d["sku"], d["product_name"], d["category"],
                 d["unit_cost"], d["unit_price"], d["active_flag"])
                for d in data["products"]
            ],
        ),
        (
            "warehouses",
            "INSERT INTO warehouses VALUES (?,?,?,?)",
            [
                (d["warehouse_id"], d["warehouse_name"], d["city"], d["state"])
                for d in data["warehouses"]
            ],
        ),
        (
            "inventory",
            "INSERT INTO inventory VALUES (?,?,?,?,?,?)",
            [
                (d["inventory_id"], d["warehouse_id"], d["product_id"],
                 d["quantity_on_hand"], d["reorder_point"], d["last_updated"])
                for d in data["inventory"]
            ],
        ),
        (
            "sales_orders",
            "INSERT INTO sales_orders VALUES (?,?,?,?,?,?,?)",
            [
                (d["order_id"], d["customer_id"], d["order_date"],
                 d["order_status"], d["requested_ship_date"],
                 d["actual_ship_date"], d["total_amount"])
                for d in data["orders"]
            ],
        ),
        (
            "sales_order_items",
            "INSERT INTO sales_order_items VALUES (?,?,?,?,?,?)",
            [
                (d["order_item_id"], d["order_id"], d["product_id"],
                 d["quantity"], d["unit_price"], d["line_total"])
                for d in data["order_items"]
            ],
        ),
        (
            "shipments",
            "INSERT INTO shipments VALUES (?,?,?,?,?,?)",
            [
                (d["shipment_id"], d["order_id"], d["warehouse_id"],
                 d["shipment_date"], d["delivery_date"], d["shipment_status"])
                for d in data["shipments"]
            ],
        ),
        (
            "invoices",
            "INSERT INTO invoices VALUES (?,?,?,?,?,?)",
            [
                (d["invoice_id"], d["order_id"], d["invoice_date"],
                 d["due_date"], d["invoice_amount"], d["invoice_status"])
                for d in data["invoices"]
            ],
        ),
        (
            "payments",
            "INSERT INTO payments VALUES (?,?,?,?,?)",
            [
                (d["payment_id"], d["invoice_id"], d["payment_date"],
                 d["payment_amount"], d["payment_method"])
                for d in data["payments"]
            ],
        ),
    ]

    for table_name, sql, rows in inserts:
        cursor.executemany(sql, rows)
        print(f"  {table_name}: {len(rows):,} rows loaded.")

    conn.commit()
    conn.close()


# ── Step 4: Build the star schema tables ──────────────────────────────────────

def step4_build_star_schema():
    """Drop and recreate the star schema analytics tables."""
    print("\n── Step 4: Building star schema tables ─────────────────────────────")
    from build_star_schema import build_star_schema
    build_star_schema()


# ── Step 5: Load dimension tables ─────────────────────────────────────────────

def step5_load_dimensions():
    """Populate dim_customer, dim_product, dim_warehouse, dim_date."""
    from load_dimensions import load_all_dimensions
    load_all_dimensions()


# ── Step 6: Load fact tables ──────────────────────────────────────────────────

def step6_load_facts():
    """Populate fact_sales, fact_shipments, fact_payments."""
    from load_facts import load_all_facts
    load_all_facts()


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 68)
    print("  Mini ERP — Full Pipeline Build")
    print("=" * 68)

    step1_create_oltp_tables()
    step2_load_raw_erp_data()
    step4_build_star_schema()
    step5_load_dimensions()
    step6_load_facts()

    print("\n" + "=" * 68)
    print("  Pipeline complete.")
    print("  Launch the dashboard with:")
    print("    streamlit run app/streamlit_app.py")
    print("=" * 68)

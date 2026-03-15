# etl/build_star_schema.py
# Creates (or safely rebuilds) all star schema tables in erp.db.
#
# Run this BEFORE loading dimensions and facts.
#
# How it works:
#   1. Reads sql/star_schema.sql, which starts with DROP TABLE IF EXISTS
#      statements for each table, so re-running is always safe.
#   2. Executes the DDL against the same erp.db that holds the OLTP tables.
#   3. Does NOT touch any existing OLTP tables (customers, sales_orders, etc.).

from etl_utils import get_conn, SQL_DIR


def build_star_schema():
    """Drop and recreate all star schema tables from sql/star_schema.sql."""

    sql_path = SQL_DIR / "star_schema.sql"
    print(f"Reading star schema DDL: {sql_path.name}")

    with open(sql_path, "r") as f:
        ddl = f.read()

    conn = get_conn()
    try:
        # executescript() commits any open transaction before running the DDL,
        # which is required for CREATE/DROP statements in SQLite.
        conn.executescript(ddl)
        print("Star schema tables created successfully.")
        print("  Tables: dim_customer, dim_product, dim_warehouse, dim_date,")
        print("          fact_sales, fact_shipments, fact_payments")
    finally:
        conn.close()


if __name__ == "__main__":
    build_star_schema()

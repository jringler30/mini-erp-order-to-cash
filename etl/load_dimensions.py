# etl/load_dimensions.py
# Populates the four dimension tables from OLTP source tables.
#
# Loading strategy: full refresh (DELETE → INSERT) on every ETL run.
# This keeps the logic simple and is fine for datasets of this size.
#
# Surrogate key assignment:
#   For customers, products, and warehouses the surrogate key is set equal to
#   the OLTP primary key. This works because the OLTP IDs are already stable
#   integers with no gaps or reuse. In a production warehouse you would use
#   independent sequences to decouple the two layers.
#
# dim_date is built by collecting every distinct date that appears anywhere
# in the OLTP tables, expanding the range to cover every calendar day in
# between, and inserting one row per day.

from datetime import date
from etl_utils import get_conn, date_to_key, daterange


# ── dim_customer ───────────────────────────────────────────────────────────────

def load_dim_customer(conn):
    """Copy customer attributes from the OLTP customers table."""
    print("  Loading dim_customer...")
    conn.execute("DELETE FROM dim_customer")

    rows = conn.execute("""
        SELECT customer_id, customer_name, customer_email,
               region, industry, created_date
        FROM customers
        ORDER BY customer_id
    """).fetchall()

    insert_rows = [
        (
            r["customer_id"],    # customer_key  (surrogate = natural key here)
            r["customer_id"],    # customer_id   (kept for traceability)
            r["customer_name"],
            r["customer_email"],
            r["region"],
            r["industry"],
            r["created_date"],
        )
        for r in rows
    ]

    conn.executemany(
        "INSERT INTO dim_customer VALUES (?,?,?,?,?,?,?)",
        insert_rows,
    )
    print(f"    {len(insert_rows)} rows inserted.")


# ── dim_product ────────────────────────────────────────────────────────────────

def load_dim_product(conn):
    """Copy product attributes from the OLTP products table."""
    print("  Loading dim_product...")
    conn.execute("DELETE FROM dim_product")

    rows = conn.execute("""
        SELECT product_id, sku, product_name, category,
               unit_cost, unit_price, active_flag
        FROM products
        ORDER BY product_id
    """).fetchall()

    insert_rows = [
        (
            r["product_id"],     # product_key  (surrogate = natural key)
            r["product_id"],     # product_id   (kept for traceability)
            r["sku"],
            r["product_name"],
            r["category"],
            r["unit_cost"],
            r["unit_price"],
            r["active_flag"],
        )
        for r in rows
    ]

    conn.executemany(
        "INSERT INTO dim_product VALUES (?,?,?,?,?,?,?,?)",
        insert_rows,
    )
    print(f"    {len(insert_rows)} rows inserted.")


# ── dim_warehouse ──────────────────────────────────────────────────────────────

def load_dim_warehouse(conn):
    """Copy warehouse attributes from the OLTP warehouses table."""
    print("  Loading dim_warehouse...")
    conn.execute("DELETE FROM dim_warehouse")

    rows = conn.execute("""
        SELECT warehouse_id, warehouse_name, city, state
        FROM warehouses
        ORDER BY warehouse_id
    """).fetchall()

    insert_rows = [
        (
            r["warehouse_id"],   # warehouse_key (surrogate = natural key)
            r["warehouse_id"],   # warehouse_id  (kept for traceability)
            r["warehouse_name"],
            r["city"],
            r["state"],
        )
        for r in rows
    ]

    conn.executemany(
        "INSERT INTO dim_warehouse VALUES (?,?,?,?,?)",
        insert_rows,
    )
    print(f"    {len(insert_rows)} rows inserted.")


# ── dim_date ───────────────────────────────────────────────────────────────────

def load_dim_date(conn):
    """Build a calendar dimension spanning every date found in the OLTP data.

    Steps:
      1. Collect every distinct date from sales_orders, shipments, invoices,
         and payments (both start dates and end dates like due_date).
      2. Find the minimum and maximum dates across all of those.
      3. Generate one row for every calendar day in that range — this ensures
         there are no gaps, so every date key in a fact table has a matching
         row in dim_date.
    """
    print("  Loading dim_date...")
    conn.execute("DELETE FROM dim_date")

    # Pull all date columns from every OLTP table that contains dates
    date_queries = [
        "SELECT order_date          AS d FROM sales_orders WHERE order_date IS NOT NULL",
        "SELECT actual_ship_date    AS d FROM sales_orders WHERE actual_ship_date IS NOT NULL",
        "SELECT shipment_date       AS d FROM shipments    WHERE shipment_date IS NOT NULL",
        "SELECT delivery_date       AS d FROM shipments    WHERE delivery_date IS NOT NULL",
        "SELECT invoice_date        AS d FROM invoices     WHERE invoice_date IS NOT NULL",
        "SELECT due_date            AS d FROM invoices     WHERE due_date IS NOT NULL",
        "SELECT payment_date        AS d FROM payments     WHERE payment_date IS NOT NULL",
    ]

    all_dates = set()
    for q in date_queries:
        for row in conn.execute(q).fetchall():
            if row["d"]:
                # Keep only the YYYY-MM-DD portion (strip any time component)
                all_dates.add(str(row["d"])[:10])

    if not all_dates:
        print("    No dates found in source data — dim_date will be empty.")
        return

    min_date = date.fromisoformat(min(all_dates))
    max_date = date.fromisoformat(max(all_dates))
    print(f"    Date range: {min_date} → {max_date}")

    # Lookup tables for human-readable names
    day_names   = ["Monday", "Tuesday", "Wednesday", "Thursday",
                   "Friday", "Saturday", "Sunday"]
    month_names = ["",  # index 0 unused — months are 1-12
                   "January", "February", "March", "April",
                   "May", "June", "July", "August",
                   "September", "October", "November", "December"]

    insert_rows = []
    for d in daterange(min_date, max_date):
        date_key     = int(d.strftime("%Y%m%d"))   # e.g. 20240115
        full_date    = d.isoformat()                # e.g. '2024-01-15'
        year         = d.year
        month        = d.month
        day          = d.day
        quarter      = (month - 1) // 3 + 1        # 1, 2, 3, or 4
        month_name   = month_names[month]

        # Python's weekday(): 0 = Monday … 6 = Sunday
        # Standard DW convention: 0 = Sunday … 6 = Saturday
        dow_monday   = d.weekday()                  # 0 = Mon, 6 = Sun
        day_of_week  = (dow_monday + 1) % 7         # 0 = Sun, 6 = Sat
        day_name     = day_names[dow_monday]

        # %W: week number where Monday is the first day; week 0 before first Mon
        week_of_year = int(d.strftime("%W"))

        insert_rows.append((
            date_key, full_date, year, quarter, month,
            month_name, day, day_of_week, day_name, week_of_year,
        ))

    conn.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?,?,?,?,?,?,?)",
        insert_rows,
    )
    print(f"    {len(insert_rows)} rows inserted.")


# ── Orchestrator ───────────────────────────────────────────────────────────────

def load_all_dimensions():
    """Run all four dimension loads inside a single transaction."""
    print("\n── Loading dimensions ──────────────────────────────────────────────")
    conn = get_conn()
    try:
        load_dim_customer(conn)
        load_dim_product(conn)
        load_dim_warehouse(conn)
        load_dim_date(conn)
        conn.commit()
        print("All dimensions loaded.")
    finally:
        conn.close()


if __name__ == "__main__":
    load_all_dimensions()

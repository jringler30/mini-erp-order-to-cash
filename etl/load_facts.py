# etl/load_facts.py
# Populates the three fact tables from OLTP transactional tables.
#
# Loading strategy: full refresh (DELETE → INSERT) on every ETL run.
#
# Calculated fields are computed here during the ETL rather than in views,
# so analysts can filter and aggregate on them without re-running the math:
#
#   fact_sales:     extended_amount = quantity × unit_price
#                   extended_cost   = quantity × unit_cost
#
#   fact_shipments: days_to_ship    = shipment_date − order_date
#                   days_to_deliver = delivery_date − shipment_date
#
#   fact_payments:  days_to_pay     = payment_date − invoice_date
#
# Foreign key values (customer_key, product_key, etc.) are looked up by
# joining to the OLTP tables. Since surrogate keys equal natural keys in
# this project, the join is straightforward.

from etl_utils import get_conn, date_to_key


# ── fact_sales ─────────────────────────────────────────────────────────────────

def load_fact_sales(conn):
    """One row per sales order line item.

    Grain: sales_order_items.order_item_id

    The warehouse comes from the first shipment on each order (orders may have
    zero or one shipment in this dataset). A LEFT JOIN is used so that orders
    with no shipment yet (status = Pending or Cancelled) still appear in the
    fact table — their warehouse_key and ship_date_key will be NULL.
    """
    print("  Loading fact_sales...")
    conn.execute("DELETE FROM fact_sales")

    rows = conn.execute("""
        SELECT
            oi.order_item_id,
            oi.order_id,
            o.customer_id                               AS customer_key,
            oi.product_id                               AS product_key,
            s.warehouse_id                              AS warehouse_key,
            o.order_date,
            s.shipment_date                             AS ship_date,
            oi.quantity,
            oi.unit_price,
            p.unit_cost,
            ROUND(oi.quantity * oi.unit_price, 4)       AS extended_amount,
            ROUND(oi.quantity * p.unit_cost,   4)       AS extended_cost,
            o.order_status
        FROM sales_order_items oi
        JOIN sales_orders o  ON oi.order_id   = o.order_id
        JOIN products     p  ON oi.product_id = p.product_id
        LEFT JOIN (
            -- Use the first shipment per order.
            -- Most orders have exactly one shipment, but the subquery protects
            -- against edge cases where there could be more than one.
            SELECT order_id, warehouse_id, shipment_date
            FROM shipments
            WHERE rowid IN (
                SELECT MIN(rowid)
                FROM shipments
                GROUP BY order_id
            )
        ) s ON o.order_id = s.order_id
    """).fetchall()

    insert_rows = [
        (
            None,                               # fact_sales_id — auto-assigned by SQLite
            r["order_item_id"],
            r["order_id"],
            r["customer_key"],
            r["product_key"],
            r["warehouse_key"],                 # NULL for unshipped orders
            date_to_key(r["order_date"]),
            date_to_key(r["ship_date"]),        # NULL for unshipped orders
            r["quantity"],
            r["unit_price"],
            r["unit_cost"],
            r["extended_amount"],
            r["extended_cost"],
            r["order_status"],
        )
        for r in rows
    ]

    conn.executemany(
        "INSERT INTO fact_sales VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        insert_rows,
    )
    print(f"    {len(insert_rows)} rows inserted.")


# ── fact_shipments ─────────────────────────────────────────────────────────────

def load_fact_shipments(conn):
    """One row per shipment record.

    Grain: shipments.shipment_id

    days_to_ship    = how many days from order placement to shipment dispatch.
    days_to_deliver = how many days from dispatch to delivery at customer.

    SQLite's julianday() converts dates to a floating-point day number, so
    subtracting two julianday values gives the difference in days. CAST to
    INTEGER drops the fractional part (partial days are not meaningful here).
    Both fields are NULL when the corresponding date is NULL (e.g. a shipment
    that has not yet been delivered has no delivery_date).
    """
    print("  Loading fact_shipments...")
    conn.execute("DELETE FROM fact_shipments")

    rows = conn.execute("""
        SELECT
            s.shipment_id,
            s.order_id,
            s.warehouse_id                                              AS warehouse_key,
            s.shipment_date,
            s.delivery_date,
            o.order_date,
            s.shipment_status,
            CAST(
                julianday(s.shipment_date) - julianday(o.order_date)
                AS INTEGER
            )                                                           AS days_to_ship,
            CAST(
                julianday(s.delivery_date) - julianday(s.shipment_date)
                AS INTEGER
            )                                                           AS days_to_deliver
        FROM shipments s
        JOIN sales_orders o ON s.order_id = o.order_id
    """).fetchall()

    insert_rows = [
        (
            None,                                   # fact_shipment_id — auto-assigned
            r["shipment_id"],
            r["order_id"],
            r["warehouse_key"],
            date_to_key(r["shipment_date"]),
            date_to_key(r["delivery_date"]),        # NULL if not yet delivered
            date_to_key(r["order_date"]),
            r["shipment_status"],
            r["days_to_ship"],
            r["days_to_deliver"],
        )
        for r in rows
    ]

    conn.executemany(
        "INSERT INTO fact_shipments VALUES (?,?,?,?,?,?,?,?,?,?)",
        insert_rows,
    )
    print(f"    {len(insert_rows)} rows inserted.")


# ── fact_payments ──────────────────────────────────────────────────────────────

def load_fact_payments(conn):
    """One row per payment record.

    Grain: payments.payment_id

    days_to_pay = how many days elapsed from invoice date to when the customer
                  actually paid. A high average here signals slow collections.

    invoice_amount is denormalized into the fact so payment coverage can be
    calculated in a single table scan:
        coverage = SUM(payment_amount) / SUM(invoice_amount)
    """
    print("  Loading fact_payments...")
    conn.execute("DELETE FROM fact_payments")

    rows = conn.execute("""
        SELECT
            p.payment_id,
            p.invoice_id,
            i.order_id,
            o.customer_id                                               AS customer_key,
            p.payment_date,
            i.invoice_date,
            i.due_date,
            p.payment_amount,
            i.invoice_amount,
            p.payment_method,
            CAST(
                julianday(p.payment_date) - julianday(i.invoice_date)
                AS INTEGER
            )                                                           AS days_to_pay
        FROM payments p
        JOIN invoices     i ON p.invoice_id = i.invoice_id
        JOIN sales_orders o ON i.order_id   = o.order_id
    """).fetchall()

    insert_rows = [
        (
            None,                                   # fact_payment_id — auto-assigned
            r["payment_id"],
            r["invoice_id"],
            r["order_id"],
            r["customer_key"],
            date_to_key(r["payment_date"]),
            date_to_key(r["invoice_date"]),
            date_to_key(r["due_date"]),
            r["payment_amount"],
            r["invoice_amount"],
            r["payment_method"],
            r["days_to_pay"],
        )
        for r in rows
    ]

    conn.executemany(
        "INSERT INTO fact_payments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        insert_rows,
    )
    print(f"    {len(insert_rows)} rows inserted.")


# ── Orchestrator ───────────────────────────────────────────────────────────────

def load_all_facts():
    """Run all three fact loads inside a single transaction."""
    print("\n── Loading facts ───────────────────────────────────────────────────")
    conn = get_conn()
    try:
        load_fact_sales(conn)
        load_fact_shipments(conn)
        load_fact_payments(conn)
        conn.commit()
        print("All facts loaded.")
    finally:
        conn.close()


if __name__ == "__main__":
    load_all_facts()

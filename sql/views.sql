-- sql/views.sql
-- Reusable reporting views.

-- ─────────────────────────────────────────
-- 1. vw_order_summary
-- One row per order with customer info and order details
-- ─────────────────────────────────────────
CREATE VIEW vw_order_summary AS
    SELECT
        o.order_id,
        o.order_date,
        o.order_status,
        o.total_amount,
        c.customer_name,
        c.region,
        c.industry
    FROM sales_orders o
    JOIN customers c ON o.customer_id = c.customer_id
    ORDER BY o.order_date DESC;


-- ─────────────────────────────────────────
-- 2. vw_invoice_payment_status
-- Invoice totals, payment totals, and unpaid balance per invoice
-- ─────────────────────────────────────────
CREATE VIEW vw_invoice_payment_status AS
    SELECT
        i.invoice_id,
        i.invoice_date,
        i.due_date,
        i.invoice_status,
        i.invoice_amount,
        COALESCE(SUM(p.payment_amount), 0)                AS amount_paid,
        i.invoice_amount - COALESCE(SUM(p.payment_amount), 0) AS balance_due,
        c.customer_name
    FROM invoices i
    JOIN sales_orders o ON i.order_id    = o.order_id
    JOIN customers    c ON o.customer_id = c.customer_id
    LEFT JOIN payments p ON i.invoice_id = p.invoice_id
    GROUP BY i.invoice_id;


-- ─────────────────────────────────────────
-- 3. vw_inventory_status
-- Stock levels per product per warehouse with low stock flag
-- ─────────────────────────────────────────
CREATE VIEW vw_inventory_status AS
    SELECT
        p.product_name,
        p.category,
        w.warehouse_name,
        w.city,
        w.state,
        inv.quantity_on_hand,
        inv.reorder_point,
        CASE WHEN inv.quantity_on_hand <= inv.reorder_point
             THEN 1 ELSE 0
        END AS low_stock_flag
    FROM inventory inv
    JOIN products   p ON inv.product_id   = p.product_id
    JOIN warehouses w ON inv.warehouse_id = w.warehouse_id
    ORDER BY low_stock_flag DESC, inv.quantity_on_hand ASC;


-- ─────────────────────────────────────────
-- 4. vw_customer_lifetime_value
-- Total revenue per customer across all paid orders
-- ─────────────────────────────────────────
CREATE VIEW vw_customer_lifetime_value AS
    SELECT
        c.customer_id,
        c.customer_name,
        c.region,
        c.industry,
        COUNT(o.order_id)               AS total_orders,
        ROUND(SUM(o.total_amount), 2)   AS lifetime_value
    FROM customers c
    JOIN sales_orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'Paid'
    GROUP BY c.customer_id
    ORDER BY lifetime_value DESC;

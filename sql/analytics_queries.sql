-- sql/analytics_queries.sql
-- Business-facing analytics queries.

-- ─────────────────────────────────────────
-- 1. Revenue by month
-- How much revenue did we make each month?
-- ─────────────────────────────────────────
SELECT
    strftime('%Y-%m', order_date) AS month,
    SUM(total_amount)             AS revenue
FROM sales_orders
WHERE order_status = 'Paid'
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month ASC;


-- ─────────────────────────────────────────
-- 2. Revenue by product
-- Which products generate the most revenue?
-- ─────────────────────────────────────────
SELECT
    p.product_name,
    p.category,
    SUM(oi.line_total) AS revenue
FROM sales_order_items oi
JOIN products     p ON oi.product_id = p.product_id
JOIN sales_orders o ON oi.order_id   = o.order_id
WHERE o.order_status = 'Paid'
GROUP BY p.product_id
ORDER BY revenue DESC;


-- ─────────────────────────────────────────
-- 3. Revenue by customer
-- Who are the top customers by revenue?
-- ─────────────────────────────────────────
SELECT
    c.customer_name,
    c.region,
    c.industry,
    SUM(o.total_amount) AS revenue,
    COUNT(o.order_id)   AS total_orders
FROM sales_orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'Paid'
GROUP BY c.customer_id
ORDER BY revenue DESC;


-- ─────────────────────────────────────────
-- 4. Open invoices
-- Which invoices are still unpaid or overdue?
-- ─────────────────────────────────────────
SELECT
    i.invoice_id,
    c.customer_name,
    i.invoice_date,
    i.due_date,
    i.invoice_amount,
    i.invoice_status
FROM invoices i
JOIN sales_orders o ON i.order_id   = o.order_id
JOIN customers    c ON o.customer_id = c.customer_id
WHERE i.invoice_status IN ('Unpaid', 'Overdue')
ORDER BY i.due_date ASC;


-- ─────────────────────────────────────────
-- 5. Inventory at risk
-- Which products are at or below their reorder point?
-- ─────────────────────────────────────────
SELECT
    p.product_name,
    p.category,
    w.warehouse_name,
    inv.quantity_on_hand,
    inv.reorder_point,
    inv.quantity_on_hand - inv.reorder_point AS stock_gap
FROM inventory inv
JOIN products   p ON inv.product_id   = p.product_id
JOIN warehouses w ON inv.warehouse_id = w.warehouse_id
WHERE inv.quantity_on_hand <= inv.reorder_point
ORDER BY stock_gap ASC;


-- ─────────────────────────────────────────
-- 6. Average days from order to shipment
-- How fast are we fulfilling orders?
-- ─────────────────────────────────────────
SELECT
    ROUND(AVG(
        julianday(s.shipment_date) - julianday(o.order_date)
    ), 1) AS avg_days_to_ship
FROM sales_orders o
JOIN shipments s ON o.order_id = s.order_id
WHERE s.shipment_date IS NOT NULL;


-- ─────────────────────────────────────────
-- 7. Average days from invoice to payment
-- How quickly are customers paying?
-- ─────────────────────────────────────────
SELECT
    ROUND(AVG(
        julianday(p.payment_date) - julianday(i.invoice_date)
    ), 1) AS avg_days_to_payment
FROM invoices i
JOIN payments p ON i.invoice_id = p.invoice_id;


-- ─────────────────────────────────────────
-- 8. Order status breakdown
-- How many orders are in each status?
-- ─────────────────────────────────────────
SELECT
    order_status,
    COUNT(order_id)             AS order_count,
    ROUND(SUM(total_amount), 2) AS total_value
FROM sales_orders
GROUP BY order_status
ORDER BY order_count DESC;

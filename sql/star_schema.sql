-- sql/star_schema.sql
-- Star schema (OLAP analytics layer) for the Mini ERP system.
--
-- These tables live in the same erp.db database alongside the OLTP tables.
-- The ETL pipeline (etl/) reads from the OLTP tables and populates these.
--
-- Architecture:
--   OLTP tables (customers, sales_orders, etc.)
--       ↓  ETL pipeline
--   Star schema tables (dim_*, fact_*)
--       ↓  Streamlit dashboard queries

-- ─────────────────────────────────────────────────────────────────────────────
-- DROP existing star schema tables so this file is safe to re-run.
-- Facts first (they reference dimensions), then dimensions.
-- ─────────────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS fact_payments;
DROP TABLE IF EXISTS fact_shipments;
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_warehouse;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;

-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION TABLES
-- Each dimension holds descriptive attributes (the "who, what, where, when").
-- Surrogate integer primary keys are used; the original source IDs are kept
-- as separate columns so ETL joins back to the OLTP layer stay readable.
-- ─────────────────────────────────────────────────────────────────────────────

-- dim_customer: one row per customer
CREATE TABLE dim_customer (
    customer_key    INTEGER  PRIMARY KEY,   -- surrogate key (assigned by ETL)
    customer_id     INTEGER  NOT NULL,      -- natural key from OLTP customers table
    customer_name   TEXT     NOT NULL,
    customer_email  TEXT     NOT NULL,
    region          TEXT     NOT NULL,      -- North / South / East / West
    industry        TEXT     NOT NULL,
    created_date    DATE     NOT NULL
);

-- dim_product: one row per product
CREATE TABLE dim_product (
    product_key   INTEGER  PRIMARY KEY,     -- surrogate key
    product_id    INTEGER  NOT NULL,        -- natural key from OLTP products table
    sku           TEXT     NOT NULL,
    product_name  TEXT     NOT NULL,
    category      TEXT     NOT NULL,
    unit_cost     REAL     NOT NULL,        -- cost to the company
    unit_price    REAL     NOT NULL,        -- price charged to customer
    active_flag   INTEGER  NOT NULL         -- 1 = active, 0 = discontinued
);

-- dim_warehouse: one row per fulfillment warehouse
CREATE TABLE dim_warehouse (
    warehouse_key   INTEGER  PRIMARY KEY,   -- surrogate key
    warehouse_id    INTEGER  NOT NULL,      -- natural key from OLTP warehouses table
    warehouse_name  TEXT     NOT NULL,
    city            TEXT     NOT NULL,
    state           TEXT     NOT NULL
);

-- dim_date: one row per calendar day, covering the full date range in the data.
-- The primary key is an integer in YYYYMMDD format (e.g. 20240115).
-- This makes date-range filtering fast and human-readable in SQL.
CREATE TABLE dim_date (
    date_key        INTEGER  PRIMARY KEY,   -- e.g. 20240115
    full_date       DATE     NOT NULL,      -- e.g. '2024-01-15'
    year            INTEGER  NOT NULL,      -- e.g. 2024
    quarter         INTEGER  NOT NULL,      -- 1 through 4
    month           INTEGER  NOT NULL,      -- 1 through 12
    month_name      TEXT     NOT NULL,      -- 'January', 'February', ...
    day             INTEGER  NOT NULL,      -- 1 through 31
    day_of_week     INTEGER  NOT NULL,      -- 0 = Sunday, 6 = Saturday
    day_name        TEXT     NOT NULL,      -- 'Monday', 'Tuesday', ...
    week_of_year    INTEGER  NOT NULL       -- ISO week number 1–53
);

-- ─────────────────────────────────────────────────────────────────────────────
-- FACT TABLES
-- Facts hold the measurable events (the "how much, how many, how long").
-- Foreign keys point to dimension surrogate keys.
-- ─────────────────────────────────────────────────────────────────────────────

-- fact_sales: grain = one sales order line item
-- Use this table to answer revenue, volume, and margin questions.
CREATE TABLE fact_sales (
    fact_sales_id     INTEGER  PRIMARY KEY,

    -- Natural keys (kept for traceability back to OLTP)
    order_item_id     INTEGER  NOT NULL,
    order_id          INTEGER  NOT NULL,

    -- Dimension foreign keys
    customer_key      INTEGER  REFERENCES dim_customer(customer_key),
    product_key       INTEGER  REFERENCES dim_product(product_key),
    warehouse_key     INTEGER  REFERENCES dim_warehouse(warehouse_key),  -- NULL if no shipment yet
    order_date_key    INTEGER  REFERENCES dim_date(date_key),
    ship_date_key     INTEGER  REFERENCES dim_date(date_key),            -- NULL if not yet shipped

    -- Measures
    quantity          INTEGER  NOT NULL,
    unit_price        REAL     NOT NULL,
    unit_cost         REAL     NOT NULL,
    extended_amount   REAL     NOT NULL,    -- quantity × unit_price  (revenue line)
    extended_cost     REAL     NOT NULL,    -- quantity × unit_cost   (COGS line)
    order_status      TEXT     NOT NULL
);

-- fact_shipments: grain = one shipment record
-- Use this table to answer fulfillment speed and warehouse throughput questions.
CREATE TABLE fact_shipments (
    fact_shipment_id  INTEGER  PRIMARY KEY,

    -- Natural keys
    shipment_id       INTEGER  NOT NULL,
    order_id          INTEGER  NOT NULL,

    -- Dimension foreign keys
    warehouse_key     INTEGER  REFERENCES dim_warehouse(warehouse_key),
    ship_date_key     INTEGER  REFERENCES dim_date(date_key),
    delivery_date_key INTEGER  REFERENCES dim_date(date_key),
    order_date_key    INTEGER  REFERENCES dim_date(date_key),

    -- Measures
    shipment_status   TEXT     NOT NULL,
    days_to_ship      INTEGER,              -- shipment_date − order_date (NULL if date missing)
    days_to_deliver   INTEGER              -- delivery_date − shipment_date (NULL if not delivered)
);

-- fact_payments: grain = one payment record
-- Use this table to answer cash collection speed and AR aging questions.
CREATE TABLE fact_payments (
    fact_payment_id   INTEGER  PRIMARY KEY,

    -- Natural keys
    payment_id        INTEGER  NOT NULL,
    invoice_id        INTEGER  NOT NULL,
    order_id          INTEGER  NOT NULL,

    -- Dimension foreign keys
    customer_key      INTEGER  REFERENCES dim_customer(customer_key),
    payment_date_key  INTEGER  REFERENCES dim_date(date_key),
    invoice_date_key  INTEGER  REFERENCES dim_date(date_key),
    due_date_key      INTEGER  REFERENCES dim_date(date_key),

    -- Measures
    payment_amount    REAL     NOT NULL,
    invoice_amount    REAL     NOT NULL,
    payment_method    TEXT     NOT NULL,
    days_to_pay       INTEGER             -- payment_date − invoice_date
);

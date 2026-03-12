-- sql/schema.sql
-- ERP Order-to-Cash relational schema for SQLite.

-- ─────────────────────────────────────────
-- ROUND 1: Foundation tables (no foreign keys)
-- ─────────────────────────────────────────

CREATE TABLE customers (
    customer_id     INTEGER  PRIMARY KEY,
    customer_name   TEXT     NOT NULL,
    customer_email  TEXT     NOT NULL UNIQUE,
    region          TEXT     NOT NULL CHECK(region IN ('North', 'South', 'East', 'West')),
    industry        TEXT     NOT NULL,
    created_date    DATE     NOT NULL
);

CREATE TABLE products (
    product_id    INTEGER  PRIMARY KEY,
    sku           TEXT     NOT NULL UNIQUE,
    product_name  TEXT     NOT NULL,
    category      TEXT     NOT NULL,
    unit_cost     REAL     NOT NULL CHECK(unit_cost >= 0),
    unit_price    REAL     NOT NULL CHECK(unit_price >= 0),
    active_flag   INTEGER  NOT NULL DEFAULT 1 CHECK(active_flag IN (0, 1))
);

CREATE TABLE warehouses (
    warehouse_id    INTEGER  PRIMARY KEY,
    warehouse_name  TEXT     NOT NULL,
    city            TEXT     NOT NULL,
    state           TEXT     NOT NULL
);

-- ─────────────────────────────────────────
-- ROUND 2: Depend on foundation tables
-- ─────────────────────────────────────────

CREATE TABLE inventory (
    inventory_id     INTEGER  PRIMARY KEY,
    warehouse_id     INTEGER  NOT NULL,
    product_id       INTEGER  NOT NULL,
    quantity_on_hand INTEGER  NOT NULL DEFAULT 0 CHECK(quantity_on_hand >= 0),
    reorder_point    INTEGER  NOT NULL DEFAULT 0 CHECK(reorder_point >= 0),
    last_updated     DATE     NOT NULL,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    FOREIGN KEY (product_id)   REFERENCES products(product_id)
);

CREATE TABLE sales_orders (
    order_id            INTEGER  PRIMARY KEY,
    customer_id         INTEGER  NOT NULL,
    order_date          DATE     NOT NULL,
    order_status        TEXT     NOT NULL CHECK(order_status IN ('Pending', 'Shipped', 'Invoiced', 'Paid', 'Cancelled')),
    requested_ship_date DATE,
    actual_ship_date    DATE,
    total_amount        REAL     NOT NULL DEFAULT 0 CHECK(total_amount >= 0),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ─────────────────────────────────────────
-- ROUND 3: Depend on round 2 tables
-- ─────────────────────────────────────────

CREATE TABLE sales_order_items (
    order_item_id  INTEGER  PRIMARY KEY,
    order_id       INTEGER  NOT NULL,
    product_id     INTEGER  NOT NULL,
    quantity       INTEGER  NOT NULL CHECK(quantity > 0),
    unit_price     REAL     NOT NULL CHECK(unit_price >= 0),
    line_total     REAL     NOT NULL CHECK(line_total >= 0),
    FOREIGN KEY (order_id)   REFERENCES sales_orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE shipments (
    shipment_id      INTEGER  PRIMARY KEY,
    order_id         INTEGER  NOT NULL,
    warehouse_id     INTEGER  NOT NULL,
    shipment_date    DATE,
    delivery_date    DATE,
    shipment_status  TEXT     NOT NULL CHECK(shipment_status IN ('Pending', 'Shipped', 'Delivered')),
    FOREIGN KEY (order_id)     REFERENCES sales_orders(order_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

CREATE TABLE invoices (
    invoice_id      INTEGER  PRIMARY KEY,
    order_id        INTEGER  NOT NULL,
    invoice_date    DATE     NOT NULL,
    due_date        DATE     NOT NULL,
    invoice_amount  REAL     NOT NULL CHECK(invoice_amount >= 0),
    invoice_status  TEXT     NOT NULL CHECK(invoice_status IN ('Unpaid', 'Paid', 'Overdue')),
    FOREIGN KEY (order_id) REFERENCES sales_orders(order_id)
);

-- ─────────────────────────────────────────
-- ROUND 4: Depend on round 3 tables
-- ─────────────────────────────────────────

CREATE TABLE payments (
    payment_id      INTEGER  PRIMARY KEY,
    invoice_id      INTEGER  NOT NULL,
    payment_date    DATE     NOT NULL,
    payment_amount  REAL     NOT NULL CHECK(payment_amount > 0),
    payment_method  TEXT     NOT NULL CHECK(payment_method IN ('Credit Card', 'Bank Transfer', 'Check', 'Cash')),
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
);

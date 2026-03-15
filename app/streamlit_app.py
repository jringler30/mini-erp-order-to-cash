# app/streamlit_app.py
# Mini ERP Order-to-Cash Analytics Dashboard

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

st.set_page_config(
    page_title="Mini ERP Dashboard",
    page_icon="📦",
    layout="wide"
)

import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "..", "data", "erp.db")

# ─────────────────────────────────────────
# AUTO-BUILD DATABASE ON FIRST LAUNCH
# ─────────────────────────────────────────

def build_database():
    """Build and populate erp.db if it doesn't exist (needed for cloud deployment).

    Runs the full pipeline in sequence:
      1. Create OLTP tables from sql/schema.sql
      2. Generate and insert synthetic ERP data
      3. Build the star schema analytics tables
      4. Load dimension tables
      5. Load fact tables
    """
    scripts_dir = os.path.join(BASE_DIR, "..", "scripts")
    sql_dir     = os.path.join(BASE_DIR, "..", "sql")
    etl_dir     = os.path.join(BASE_DIR, "..", "etl")
    db_path     = os.path.normpath(DB_PATH)

    sys.path.insert(0, os.path.normpath(scripts_dir))
    sys.path.insert(0, os.path.normpath(etl_dir))

    from generate_fake_data import generate_all

    # ── Step 1: Create OLTP tables ────────────────────────────────────────────
    schema_path = os.path.join(sql_dir, "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()

    # ── Step 2: Generate and insert ERP data ──────────────────────────────────
    data = generate_all()

    tables = [
        ("customers",         "INSERT INTO customers VALUES (?,?,?,?,?,?)",
         [(d["customer_id"], d["customer_name"], d["customer_email"],
           d["region"], d["industry"], d["created_date"]) for d in data["customers"]]),
        ("products",          "INSERT INTO products VALUES (?,?,?,?,?,?,?)",
         [(d["product_id"], d["sku"], d["product_name"], d["category"],
           d["unit_cost"], d["unit_price"], d["active_flag"]) for d in data["products"]]),
        ("warehouses",        "INSERT INTO warehouses VALUES (?,?,?,?)",
         [(d["warehouse_id"], d["warehouse_name"], d["city"], d["state"])
          for d in data["warehouses"]]),
        ("inventory",         "INSERT INTO inventory VALUES (?,?,?,?,?,?)",
         [(d["inventory_id"], d["warehouse_id"], d["product_id"],
           d["quantity_on_hand"], d["reorder_point"], d["last_updated"])
          for d in data["inventory"]]),
        ("sales_orders",      "INSERT INTO sales_orders VALUES (?,?,?,?,?,?,?)",
         [(d["order_id"], d["customer_id"], d["order_date"], d["order_status"],
           d["requested_ship_date"], d["actual_ship_date"], d["total_amount"])
          for d in data["orders"]]),
        ("sales_order_items", "INSERT INTO sales_order_items VALUES (?,?,?,?,?,?)",
         [(d["order_item_id"], d["order_id"], d["product_id"],
           d["quantity"], d["unit_price"], d["line_total"])
          for d in data["order_items"]]),
        ("shipments",         "INSERT INTO shipments VALUES (?,?,?,?,?,?)",
         [(d["shipment_id"], d["order_id"], d["warehouse_id"],
           d["shipment_date"], d["delivery_date"], d["shipment_status"])
          for d in data["shipments"]]),
        ("invoices",          "INSERT INTO invoices VALUES (?,?,?,?,?,?)",
         [(d["invoice_id"], d["order_id"], d["invoice_date"],
           d["due_date"], d["invoice_amount"], d["invoice_status"])
          for d in data["invoices"]]),
        ("payments",          "INSERT INTO payments VALUES (?,?,?,?,?)",
         [(d["payment_id"], d["invoice_id"], d["payment_date"],
           d["payment_amount"], d["payment_method"]) for d in data["payments"]]),
    ]

    for table_name, sql, rows in tables:
        cursor.executemany(sql, rows)

    conn.commit()
    conn.close()

    # ── Steps 3–5: Build and populate the star schema ─────────────────────────
    from build_star_schema import build_star_schema
    from load_dimensions   import load_all_dimensions
    from load_facts        import load_all_facts

    build_star_schema()
    load_all_dimensions()
    load_all_facts()


if not os.path.exists(os.path.normpath(DB_PATH)):
    os.makedirs(os.path.dirname(os.path.normpath(DB_PATH)), exist_ok=True)
    with st.spinner("Setting up database for first launch..."):
        build_database()

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────

st.markdown("""
<style>
    /* Hide Streamlit default white header bar */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }

    /* Page background */
    .stApp { background-color: #0f1117; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1d27;
        border-right: 1px solid #2e3248;
    }

    /* Sidebar radio button labels — make them bright and readable */
    [data-testid="stSidebar"] label {
        color: #e0e4f0 !important;
        font-size: 15px !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .stRadio p {
        color: #e0e4f0 !important;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #1a1d27;
        border: 1px solid #2e3248;
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] { color: #8b92a5 !important; font-size: 13px !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 28px !important; font-weight: 700 !important; }

    /* Section headers */
    h1 { color: #ffffff !important; font-weight: 700 !important; }
    h2, h3 { color: #e0e4f0 !important; font-weight: 600 !important; }

    /* Body text */
    p, span, div { color: #e0e4f0; }

    /* Divider */
    hr { border-color: #2e3248 !important; }

    /* Dataframe */
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

    /* Sidebar title */
    .sidebar-title {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .sidebar-sub {
        font-size: 12px;
        color: #8b92a5;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CHART THEME
# ─────────────────────────────────────────

COLORS    = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e", "#a78bfa", "#fb923c"]
BG_COLOR  = "#0f1117"
PAPER_BG  = "#1a1d27"
FONT_COLOR= "#e0e4f0"
GRID_COLOR= "#2e3248"

def chart_layout(fig, height=380):
    fig.update_layout(
        height=height,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=BG_COLOR,
        font=dict(color=FONT_COLOR, family="Inter, sans-serif"),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=FONT_COLOR)),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    )
    return fig

# ─────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────

@st.cache_data
def query(sql):
    """Query the database and return a DataFrame. Used for OLTP table queries."""
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql(sql, conn)
    conn.close()
    return df


def _star_schema_exists() -> bool:
    """Return True if the star schema analytics tables have been built."""
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='fact_sales'"
    )
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


@st.cache_data
def query_star(sql):
    """Query the star schema analytics tables and return a DataFrame.

    Falls back to returning an empty DataFrame if the star schema doesn't exist
    yet, so the app stays functional while the ETL pipeline is first running.
    """
    if not _star_schema_exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql(sql, conn)
    conn.close()
    return df

# ─────────────────────────────────────────
# ARCHITECTURE PAGE HELPERS
# ─────────────────────────────────────────

# Box geometry constants used by both diagram builders
_BOX_W    = 2.8    # box width (all tables the same)
_HEADER_H = 0.48   # height of the coloured title bar
_ROW_H    = 0.30   # height per column row
_PAD_B    = 0.18   # padding below the last column row

def _box_h(n_cols: int) -> float:
    """Total box height for a table with n_cols columns."""
    return _HEADER_H + n_cols * _ROW_H + _PAD_B


def _draw_table_box(fig, cx: float, cy: float, title: str,
                    columns: list[str], accent: str) -> dict:
    """Draw a labelled table box centred at (cx, cy).

    Column strings that contain 'PK' are highlighted gold.
    Column strings that contain 'FK' are highlighted cyan.
    Everything else uses the default muted text colour.

    Returns a dict of edge midpoints {'top', 'bottom', 'left', 'right'}
    so callers can draw connector lines between boxes.
    """
    bh = _box_h(len(columns))
    x0, x1 = cx - _BOX_W / 2, cx + _BOX_W / 2
    y0, y1 = cy - bh / 2,     cy + bh / 2

    # Body rectangle
    fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                  fillcolor="#1a1d27", line=dict(color=accent, width=2))
    # Coloured header strip
    fig.add_shape(type="rect", x0=x0, y0=y1 - _HEADER_H, x1=x1, y1=y1,
                  fillcolor=accent, line=dict(color=accent, width=2))
    # Table name
    fig.add_annotation(x=cx, y=y1 - _HEADER_H / 2,
                       text=f"<b>{title}</b>",
                       showarrow=False,
                       font=dict(color="white", size=11, family="monospace"),
                       xanchor="center", yanchor="middle")
    # Column rows
    for i, col in enumerate(columns):
        y_c = y1 - _HEADER_H - (i + 0.5) * _ROW_H
        if   "PK" in col: col_color = "#f59e0b"   # gold   — primary keys
        elif "FK" in col: col_color = "#22d3ee"   # cyan   — foreign keys
        else:             col_color = "#c4c9d6"   # silver — regular columns
        fig.add_annotation(x=x0 + 0.12, y=y_c, text=col,
                           showarrow=False,
                           font=dict(color=col_color, size=9.5, family="monospace"),
                           xanchor="left", yanchor="middle")
    return dict(top=(cx, y1), bottom=(cx, y0),
                left=(x0, cy), right=(x1, cy))


def _draw_conn(fig, p1: tuple, p2: tuple) -> None:
    """Draw a dashed connector line between two edge points."""
    fig.add_shape(type="line",
                  x0=p1[0], y0=p1[1], x1=p2[0], y1=p2[1],
                  line=dict(color="#4b5268", width=1.5, dash="dot"))


def make_star_diagram():
    """Build and return a Plotly Figure showing the star schema.

    Layout:
                     dim_date (top)
                         |
      dim_customer — fact_sales — dim_product
                         |
                   dim_warehouse (bottom)
    """
    FACT_C = "#6366f1"   # indigo  — fact tables
    DIM_C  = "#1e40af"   # blue    — dimension tables

    fig = go.Figure()
    fig.update_layout(
        height=700,
        paper_bgcolor="#1a1d27",
        plot_bgcolor="#0f1117",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False, range=[-0.4, 13.2]),
        yaxis=dict(visible=False, range=[-0.4, 13.6]),
    )

    # ── fact_sales (centre) ────────────────────────────────────────────────────
    fs = _draw_table_box(fig, 6, 6.0, "fact_sales", [
        "fact_sales_id  PK",
        "customer_key   FK",
        "product_key    FK",
        "warehouse_key  FK",
        "order_date_key FK",
        "ship_date_key  FK",
        "quantity",
        "unit_price",
        "extended_amount",
        "extended_cost",
        "order_status",
    ], FACT_C)

    # ── dim_date (top) ─────────────────────────────────────────────────────────
    dd = _draw_table_box(fig, 6, 11.0, "dim_date", [
        "date_key    PK",
        "full_date",
        "year",
        "quarter",
        "month",
        "month_name",
        "day_name",
        "week_of_year",
    ], DIM_C)

    # ── dim_customer (left) ────────────────────────────────────────────────────
    dc = _draw_table_box(fig, 1.4, 6.0, "dim_customer", [
        "customer_key  PK",
        "customer_id",
        "customer_name",
        "region",
        "industry",
    ], DIM_C)

    # ── dim_product (right) ────────────────────────────────────────────────────
    dp = _draw_table_box(fig, 10.6, 6.0, "dim_product", [
        "product_key  PK",
        "product_id",
        "product_name",
        "category",
        "unit_price",
    ], DIM_C)

    # ── dim_warehouse (bottom) ─────────────────────────────────────────────────
    dw = _draw_table_box(fig, 6, 1.2, "dim_warehouse", [
        "warehouse_key  PK",
        "warehouse_id",
        "warehouse_name",
        "city",
        "state",
    ], DIM_C)

    # ── FK connector lines ─────────────────────────────────────────────────────
    _draw_conn(fig, fs["top"],    dd["bottom"])  # fact → dim_date
    _draw_conn(fig, fs["left"],   dc["right"])   # fact → dim_customer
    _draw_conn(fig, fs["right"],  dp["left"])    # fact → dim_product
    _draw_conn(fig, fs["bottom"], dw["top"])     # fact → dim_warehouse

    # ── Legend ─────────────────────────────────────────────────────────────────
    fig.add_annotation(x=9.5, y=0.55, text="● PK = Primary key",
                       showarrow=False,
                       font=dict(color="#f59e0b", size=10, family="monospace"),
                       xanchor="left")
    fig.add_annotation(x=9.5, y=0.22, text="● FK = Foreign key",
                       showarrow=False,
                       font=dict(color="#22d3ee", size=10, family="monospace"),
                       xanchor="left")

    # ── Diagram title ──────────────────────────────────────────────────────────
    fig.add_annotation(x=6, y=13.3,
                       text="<b>Star Schema — fact_sales grain: one row per order line item</b>",
                       showarrow=False,
                       font=dict(color="#e0e4f0", size=13),
                       xanchor="center")
    return fig


def make_oltp_diagram():
    """Build and return a Plotly Figure showing the 9 OLTP tables as a node graph.

    Tables are grouped into the 4 dependency layers they were designed in.
    Edges show FK → PK relationships (child → parent).
    """
    LAYER_COLORS = {
        1: "#10b981",   # green  — foundation (no FKs)
        2: "#6366f1",   # indigo — depend on layer 1
        3: "#f59e0b",   # amber  — depend on layer 2
        4: "#f43f5e",   # rose   — depend on layer 3
    }

    node_layer = {
        "customers": 1, "products": 1, "warehouses": 1,
        "inventory": 2, "sales_orders": 2,
        "sales_order_items": 3, "shipments": 3, "invoices": 3,
        "payments": 4,
    }

    # (x, y) centres for each node
    node_pos = {
        "customers":         (2,    10.5),
        "products":          (7,    10.5),
        "warehouses":        (12,   10.5),
        "inventory":         (2,    7),
        "sales_orders":      (9.5,  7),
        "sales_order_items": (2,    3.5),
        "shipments":         (7,    3.5),
        "invoices":          (12,   3.5),
        "payments":          (7,    0.5),
    }

    # (child, parent) FK relationships
    edges = [
        ("inventory",         "warehouses"),
        ("inventory",         "products"),
        ("sales_orders",      "customers"),
        ("sales_order_items", "sales_orders"),
        ("sales_order_items", "products"),
        ("shipments",         "sales_orders"),
        ("shipments",         "warehouses"),
        ("invoices",          "sales_orders"),
        ("payments",          "invoices"),
    ]

    fig = go.Figure()
    fig.update_layout(
        height=600,
        paper_bgcolor="#1a1d27",
        plot_bgcolor="#0f1117",
        margin=dict(l=120, r=20, t=30, b=20),
        xaxis=dict(visible=False, range=[-1.5, 14.5]),
        yaxis=dict(visible=False, range=[-1.2, 12.5]),
    )

    # ── Edges (draw first so they sit behind nodes) ────────────────────────────
    for src, dst in edges:
        x0, y0 = node_pos[src]
        x1, y1 = node_pos[dst]
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(color="#3a3f55", width=1.5),
            showlegend=False, hoverinfo="none",
        ))

    # ── Nodes (annotation boxes — bgcolour gives the filled-box look) ──────────
    for table, (x, y) in node_pos.items():
        color = LAYER_COLORS[node_layer[table]]
        fig.add_annotation(
            x=x, y=y,
            text=f"<b>{table}</b>",
            showarrow=False,
            font=dict(color="white", size=10, family="monospace"),
            bgcolor=color,
            bordercolor=color,
            borderwidth=2,
            borderpad=8,
            xanchor="center",
            yanchor="middle",
        )

    # ── Layer labels (left margin) ─────────────────────────────────────────────
    layer_meta = {
        1: (10.5, "Layer 1 · Foundation",    "No foreign keys"),
        2: (7,    "Layer 2 · Transactions",  "Depend on Layer 1"),
        3: (3.5,  "Layer 3 · Fulfillment",   "Depend on Layer 2"),
        4: (0.5,  "Layer 4 · Collections",   "Depend on Layer 3"),
    }
    for layer, (y, label, sub) in layer_meta.items():
        color = LAYER_COLORS[layer]
        fig.add_annotation(x=-1.3, y=y + 0.3,
                           text=f"<b>{label}</b>",
                           showarrow=False,
                           font=dict(color=color, size=9, family="monospace"),
                           xanchor="left")
        fig.add_annotation(x=-1.3, y=y - 0.3,
                           text=sub,
                           showarrow=False,
                           font=dict(color="#8b92a5", size=8),
                           xanchor="left")
        # Dashed separator line between layers
        if layer < 4:
            sep_y = y - 1.75
            fig.add_shape(type="line",
                          x0=-1.5, y0=sep_y, x1=14.5, y1=sep_y,
                          line=dict(color="#2e3248", width=1, dash="dash"))

    fig.add_annotation(x=6.5, y=12.2,
                       text="<b>OLTP Schema — 9 tables across 4 dependency layers</b>",
                       showarrow=False,
                       font=dict(color="#e0e4f0", size=13),
                       xanchor="center")
    return fig


@st.cache_data
def get_table_meta(table_name: str):
    """Return (columns DataFrame, row_count) pulled live from erp.db.

    Uses SQLite's PRAGMA table_info which returns column metadata without
    scanning any rows — safe and fast even on large tables.
    """
    try:
        conn  = sqlite3.connect(DB_PATH)
        cols  = pd.read_sql(f"PRAGMA table_info({table_name})", conn)
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        conn.close()
        cols = cols[["name", "type", "notnull", "pk"]].rename(columns={
            "name": "Column", "type": "Type",
            "notnull": "Not Null", "pk": "PK",
        })
        cols["Not Null"] = cols["Not Null"].map({1: "✓", 0: ""})
        cols["PK"]       = cols["PK"].map({0: "", 1: "🔑"})
        return cols, count
    except Exception:
        return pd.DataFrame(), 0


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="sidebar-title">📦 Mini ERP</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Order-to-Cash Analytics</div>', unsafe_allow_html=True)

    page = st.radio("Navigation", [
        "🏠  Executive Overview",
        "📈  Sales Analytics",
        "🚚  Order Operations",
        "🧾  Invoices & Payments",
        "🏭  Inventory Monitoring",
        "🗂️  Data Architecture",
    ], label_visibility="collapsed")

    st.divider()
    st.caption("Mini ERP System · SQLite + Streamlit")

# ─────────────────────────────────────────
# PAGE 1: EXECUTIVE OVERVIEW
# ─────────────────────────────────────────

if page == "🏠  Executive Overview":
    st.title("Executive Overview")
    st.caption("High-level KPIs across the entire order-to-cash process.")
    st.divider()

    total_revenue   = query("SELECT ROUND(SUM(total_amount),2) AS val FROM sales_orders WHERE order_status = 'Paid'").iloc[0,0]
    total_orders    = query("SELECT COUNT(*) AS val FROM sales_orders").iloc[0,0]
    total_customers = query("SELECT COUNT(*) AS val FROM customers").iloc[0,0]
    unpaid_invoices = query("SELECT ROUND(SUM(invoice_amount),2) AS val FROM invoices WHERE invoice_status IN ('Unpaid','Overdue')").iloc[0,0]
    low_stock_count = query("SELECT COUNT(*) AS val FROM inventory WHERE quantity_on_hand <= reorder_point").iloc[0,0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Total Revenue",       f"${total_revenue:,.0f}")
    c2.metric("📋 Total Orders",        f"{total_orders:,}")
    c3.metric("👥 Total Customers",     f"{total_customers:,}")
    c4.metric("⚠️ Unpaid Invoices",     f"${unpaid_invoices:,.0f}")
    c5.metric("📦 Low Stock Products",  f"{low_stock_count}")

    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Monthly Revenue Trend")
        # Read from fact_sales + dim_date (star schema) for cleaner aggregation.
        # Falls back to the OLTP query automatically if ETL hasn't run yet.
        df_rev = query_star("""
            SELECT
                dd.year || '-' || printf('%02d', dd.month) AS month,
                ROUND(SUM(fs.extended_amount), 2)          AS revenue
            FROM fact_sales fs
            JOIN dim_date dd ON fs.order_date_key = dd.date_key
            WHERE fs.order_status = 'Paid'
            GROUP BY dd.year, dd.month
            ORDER BY dd.year, dd.month
        """)
        if df_rev.empty:
            df_rev = query("""
                SELECT strftime('%Y-%m', order_date) AS month,
                       ROUND(SUM(total_amount), 2)   AS revenue
                FROM sales_orders WHERE order_status = 'Paid'
                GROUP BY month ORDER BY month ASC
            """)
        fig = px.area(df_rev, x="month", y="revenue",
                      labels={"month": "", "revenue": "Revenue ($)"},
                      color_discrete_sequence=[COLORS[0]])
        fig.update_traces(fill="tozeroy", line=dict(width=2))
        st.plotly_chart(chart_layout(fig), use_container_width=True)

    with col2:
        st.subheader("Order Status")
        df_status = query("""
            SELECT order_status, COUNT(order_id) AS order_count
            FROM sales_orders GROUP BY order_status ORDER BY order_count DESC
        """)
        fig2 = px.pie(df_status, names="order_status", values="order_count",
                      hole=0.55, color_discrete_sequence=COLORS)
        fig2.update_traces(textposition="outside", textfont=dict(color=FONT_COLOR))
        st.plotly_chart(chart_layout(fig2), use_container_width=True)


# ─────────────────────────────────────────
# PAGE 2: SALES ANALYTICS
# ─────────────────────────────────────────

elif page == "📈  Sales Analytics":
    st.title("Sales Analytics")
    st.caption("Revenue breakdowns by product, customer, category, and region.")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Products by Revenue")
        # Star schema: fact_sales already has extended_amount pre-calculated,
        # so no per-row multiplication is needed at query time.
        df_prod = query_star("""
            SELECT dp.product_name,
                   ROUND(SUM(fs.extended_amount), 2) AS revenue
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_key = dp.product_key
            WHERE fs.order_status = 'Paid'
            GROUP BY dp.product_key
            ORDER BY revenue DESC
            LIMIT 10
        """)
        if df_prod.empty:
            df_prod = query("""
                SELECT p.product_name, ROUND(SUM(oi.line_total), 2) AS revenue
                FROM sales_order_items oi
                JOIN products p     ON oi.product_id = p.product_id
                JOIN sales_orders o ON oi.order_id   = o.order_id
                WHERE o.order_status = 'Paid'
                GROUP BY p.product_id ORDER BY revenue DESC LIMIT 10
            """)
        fig = px.bar(df_prod, x="revenue", y="product_name", orientation="h",
                     labels={"revenue": "Revenue ($)", "product_name": ""},
                     color="revenue", color_continuous_scale=["#6366f1", "#22d3ee"])
        fig.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(chart_layout(fig), use_container_width=True)

    with col2:
        st.subheader("Top 10 Customers by Revenue")
        # Star schema: one join to dim_customer instead of two OLTP joins.
        df_cust = query_star("""
            SELECT dc.customer_name,
                   ROUND(SUM(fs.extended_amount), 2) AS revenue
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_key = dc.customer_key
            WHERE fs.order_status = 'Paid'
            GROUP BY dc.customer_key
            ORDER BY revenue DESC
            LIMIT 10
        """)
        if df_cust.empty:
            df_cust = query("""
                SELECT c.customer_name, ROUND(SUM(o.total_amount), 2) AS revenue
                FROM sales_orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE o.order_status = 'Paid'
                GROUP BY c.customer_id ORDER BY revenue DESC LIMIT 10
            """)
        fig2 = px.bar(df_cust, x="revenue", y="customer_name", orientation="h",
                      labels={"revenue": "Revenue ($)", "customer_name": ""},
                      color="revenue", color_continuous_scale=["#f59e0b", "#f43f5e"])
        fig2.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(chart_layout(fig2), use_container_width=True)

    st.divider()

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Revenue by Category")
        # Star schema: category is a dim_product attribute — one clean join.
        df_cat = query_star("""
            SELECT dp.category,
                   ROUND(SUM(fs.extended_amount), 2) AS revenue
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_key = dp.product_key
            WHERE fs.order_status = 'Paid'
            GROUP BY dp.category
            ORDER BY revenue DESC
        """)
        if df_cat.empty:
            df_cat = query("""
                SELECT p.category, ROUND(SUM(oi.line_total), 2) AS revenue
                FROM sales_order_items oi
                JOIN products p     ON oi.product_id = p.product_id
                JOIN sales_orders o ON oi.order_id   = o.order_id
                WHERE o.order_status = 'Paid'
                GROUP BY p.category ORDER BY revenue DESC
            """)
        fig3 = px.pie(df_cat, names="category", values="revenue",
                      hole=0.45, color_discrete_sequence=COLORS)
        fig3.update_traces(textposition="outside", textfont=dict(color=FONT_COLOR))
        st.plotly_chart(chart_layout(fig3), use_container_width=True)

    with col4:
        st.subheader("Revenue by Region")
        df_region = query("""
            SELECT c.region, ROUND(SUM(o.total_amount), 2) AS revenue
            FROM sales_orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'Paid'
            GROUP BY c.region ORDER BY revenue DESC
        """)
        fig4 = px.bar(df_region, x="region", y="revenue",
                      labels={"region": "Region", "revenue": "Revenue ($)"},
                      color="region", color_discrete_sequence=COLORS)
        fig4.update_layout(showlegend=False)
        st.plotly_chart(chart_layout(fig4), use_container_width=True)


# ─────────────────────────────────────────
# PAGE 3: ORDER OPERATIONS
# ─────────────────────────────────────────

elif page == "🚚  Order Operations":
    st.title("Order Operations")
    st.caption("Order fulfillment metrics and recent order activity.")
    st.divider()

    avg_ship       = query("""
        SELECT ROUND(AVG(julianday(s.shipment_date) - julianday(o.order_date)), 1) AS val
        FROM sales_orders o JOIN shipments s ON o.order_id = s.order_id
        WHERE s.shipment_date IS NOT NULL
    """).iloc[0,0]
    pending_orders = query("SELECT COUNT(*) AS val FROM sales_orders WHERE order_status = 'Pending'").iloc[0,0]
    shipped_orders = query("SELECT COUNT(*) AS val FROM sales_orders WHERE order_status = 'Shipped'").iloc[0,0]
    paid_orders    = query("SELECT COUNT(*) AS val FROM sales_orders WHERE order_status = 'Paid'").iloc[0,0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⏱ Avg Days to Ship",  f"{avg_ship} days")
    c2.metric("🕐 Pending Orders",   f"{pending_orders:,}")
    c3.metric("🚚 Shipped Orders",   f"{shipped_orders:,}")
    c4.metric("✅ Paid Orders",      f"{paid_orders:,}")

    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Orders by Month")
        df_monthly = query("""
            SELECT strftime('%Y-%m', order_date) AS month,
                   COUNT(order_id) AS order_count
            FROM sales_orders GROUP BY month ORDER BY month ASC
        """)
        fig = px.bar(df_monthly, x="month", y="order_count",
                     labels={"month": "", "order_count": "Orders"},
                     color_discrete_sequence=[COLORS[1]])
        st.plotly_chart(chart_layout(fig), use_container_width=True)

    with col2:
        st.subheader("Status Breakdown")
        df_status = query("""
            SELECT order_status, COUNT(*) AS count
            FROM sales_orders GROUP BY order_status
        """)
        fig2 = px.pie(df_status, names="order_status", values="count",
                      hole=0.5, color_discrete_sequence=COLORS)
        fig2.update_traces(textposition="outside", textfont=dict(color=FONT_COLOR))
        st.plotly_chart(chart_layout(fig2), use_container_width=True)

    st.divider()

    st.subheader("Recent Orders")
    df_orders = query("""
        SELECT o.order_id      AS "Order ID",
               c.customer_name AS "Customer",
               o.order_date    AS "Order Date",
               o.order_status  AS "Status",
               '$' || printf('%.2f', o.total_amount) AS "Total"
        FROM sales_orders o
        JOIN customers c ON o.customer_id = c.customer_id
        ORDER BY o.order_date DESC LIMIT 50
    """)
    st.dataframe(df_orders, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────
# PAGE 4: INVOICES & PAYMENTS
# ─────────────────────────────────────────

elif page == "🧾  Invoices & Payments":
    st.title("Invoices & Payments")
    st.caption("Invoice aging, open balances, and payment trends.")
    st.divider()

    total_invoiced = query("SELECT ROUND(SUM(invoice_amount),2) AS val FROM invoices").iloc[0,0]
    total_paid     = query("SELECT ROUND(SUM(payment_amount),2) AS val FROM payments").iloc[0,0]
    total_unpaid   = query("SELECT ROUND(SUM(invoice_amount),2) AS val FROM invoices WHERE invoice_status IN ('Unpaid','Overdue')").iloc[0,0]
    avg_pay_days   = query("""
        SELECT ROUND(AVG(julianday(p.payment_date) - julianday(i.invoice_date)), 1) AS val
        FROM invoices i JOIN payments p ON i.invoice_id = p.invoice_id
    """).iloc[0,0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧾 Total Invoiced",      f"${total_invoiced:,.0f}")
    c2.metric("✅ Total Collected",     f"${total_paid:,.0f}")
    c3.metric("⚠️ Outstanding Balance", f"${total_unpaid:,.0f}")
    c4.metric("⏱ Avg Days to Pay",     f"{avg_pay_days} days")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Invoice Status Breakdown")
        df_inv_status = query("""
            SELECT invoice_status, COUNT(*) AS count,
                   ROUND(SUM(invoice_amount), 2) AS total_amount
            FROM invoices GROUP BY invoice_status
        """)
        fig = px.pie(df_inv_status, names="invoice_status", values="count",
                     hole=0.5, color_discrete_sequence=COLORS)
        fig.update_traces(textposition="outside", textfont=dict(color=FONT_COLOR))
        st.plotly_chart(chart_layout(fig), use_container_width=True)

    with col2:
        st.subheader("Monthly Payments Collected")
        df_pay_trend = query("""
            SELECT strftime('%Y-%m', payment_date) AS month,
                   ROUND(SUM(payment_amount), 2)   AS collected
            FROM payments GROUP BY month ORDER BY month ASC
        """)
        fig2 = px.area(df_pay_trend, x="month", y="collected",
                       labels={"month": "", "collected": "Collected ($)"},
                       color_discrete_sequence=[COLORS[3]])
        fig2.update_traces(fill="tozeroy", line=dict(width=2))
        st.plotly_chart(chart_layout(fig2), use_container_width=True)

    st.divider()

    st.subheader("Open Invoices")
    df_open = query("""
        SELECT i.invoice_id        AS "Invoice ID",
               c.customer_name     AS "Customer",
               i.invoice_date      AS "Invoice Date",
               i.due_date          AS "Due Date",
               '$' || printf('%.2f', i.invoice_amount) AS "Amount",
               i.invoice_status    AS "Status"
        FROM invoices i
        JOIN sales_orders o ON i.order_id    = o.order_id
        JOIN customers    c ON o.customer_id = c.customer_id
        WHERE i.invoice_status IN ('Unpaid', 'Overdue')
        ORDER BY i.due_date ASC
    """)
    st.dataframe(df_open, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────
# PAGE 5: INVENTORY MONITORING
# ─────────────────────────────────────────

elif page == "🏭  Inventory Monitoring":
    st.title("Inventory Monitoring")
    st.caption("Stock levels, reorder alerts, and warehouse breakdown.")
    st.divider()

    total_skus  = query("SELECT COUNT(DISTINCT product_id) AS val FROM inventory").iloc[0,0]
    low_stock   = query("SELECT COUNT(*) AS val FROM inventory WHERE quantity_on_hand <= reorder_point").iloc[0,0]
    total_units = query("SELECT SUM(quantity_on_hand) AS val FROM inventory").iloc[0,0]

    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Total SKUs Tracked",  f"{total_skus}")
    c2.metric("🚨 Low Stock Alerts",    f"{low_stock}")
    c3.metric("🏭 Total Units on Hand", f"{total_units:,}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Units by Warehouse")
        df_wh = query("""
            SELECT w.warehouse_name, SUM(inv.quantity_on_hand) AS total_units
            FROM inventory inv
            JOIN warehouses w ON inv.warehouse_id = w.warehouse_id
            GROUP BY w.warehouse_id ORDER BY total_units DESC
        """)
        fig = px.bar(df_wh, x="warehouse_name", y="total_units",
                     labels={"warehouse_name": "", "total_units": "Units"},
                     color="warehouse_name", color_discrete_sequence=COLORS)
        fig.update_layout(showlegend=False)
        st.plotly_chart(chart_layout(fig), use_container_width=True)

    with col2:
        st.subheader("Stock Status by Category")
        df_cat_stock = query("""
            SELECT p.category,
                   SUM(CASE WHEN inv.quantity_on_hand <= inv.reorder_point THEN 1 ELSE 0 END) AS low_stock,
                   SUM(CASE WHEN inv.quantity_on_hand >  inv.reorder_point THEN 1 ELSE 0 END) AS ok
            FROM inventory inv
            JOIN products p ON inv.product_id = p.product_id
            GROUP BY p.category
        """)
        fig2 = go.Figure(data=[
            go.Bar(name="OK",        x=df_cat_stock["category"], y=df_cat_stock["ok"],        marker_color=COLORS[3]),
            go.Bar(name="Low Stock", x=df_cat_stock["category"], y=df_cat_stock["low_stock"], marker_color=COLORS[4]),
        ])
        fig2.update_layout(barmode="stack")
        st.plotly_chart(chart_layout(fig2), use_container_width=True)

    st.divider()

    st.subheader("🚨 Low Stock Alerts")
    df_low = query("""
        SELECT p.product_name  AS "Product",
               p.category      AS "Category",
               w.warehouse_name AS "Warehouse",
               inv.quantity_on_hand AS "On Hand",
               inv.reorder_point    AS "Reorder Point",
               inv.quantity_on_hand - inv.reorder_point AS "Gap"
        FROM inventory inv
        JOIN products   p ON inv.product_id   = p.product_id
        JOIN warehouses w ON inv.warehouse_id = w.warehouse_id
        WHERE inv.quantity_on_hand <= inv.reorder_point
        ORDER BY inv.quantity_on_hand - inv.reorder_point ASC
    """)
    st.dataframe(df_low, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Full Inventory")
    df_inv = query("""
        SELECT p.product_name  AS "Product",
               p.category      AS "Category",
               w.warehouse_name AS "Warehouse",
               inv.quantity_on_hand AS "On Hand",
               inv.reorder_point    AS "Reorder Point",
               CASE WHEN inv.quantity_on_hand <= inv.reorder_point
                    THEN '🔴 Low Stock' ELSE '🟢 OK'
               END AS "Status"
        FROM inventory inv
        JOIN products   p ON inv.product_id   = p.product_id
        JOIN warehouses w ON inv.warehouse_id = w.warehouse_id
        ORDER BY p.product_name
    """)
    st.dataframe(df_inv, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────
# PAGE 6: DATA ARCHITECTURE
# ─────────────────────────────────────────

elif page == "🗂️  Data Architecture":
    st.title("Data Architecture")
    st.caption("Interactive reference for the OLTP transactional layer and the star schema analytics layer.")
    st.divider()

    tab_star, tab_oltp = st.tabs(["⭐  Star Schema (OLAP)", "🔗  OLTP Transactional Layer"])

    # ── Tab 1: Star Schema ─────────────────────────────────────────────────────
    with tab_star:
        st.markdown(
            "The ETL pipeline reads from the OLTP tables and writes into these seven tables. "
            "Key dashboard charts query the fact and dimension tables directly."
        )

        st.plotly_chart(make_star_diagram(), use_container_width=True)

        st.divider()
        st.subheader("Row Counts")

        star_tables = [
            "fact_sales", "fact_shipments", "fact_payments",
            "dim_customer", "dim_product", "dim_warehouse", "dim_date",
        ]
        metric_cols = st.columns(len(star_tables))
        for col, tname in zip(metric_cols, star_tables):
            _, count = get_table_meta(tname)
            # Shorten label to fit the card width
            short = tname.replace("fact_", "").replace("dim_", "")
            col.metric(short, f"{count:,}")

        st.divider()
        st.subheader("Column Reference")
        st.caption("Expand any table to see its full column list pulled live from the database.")

        # Group facts and dims visually
        fact_col, dim_col = st.columns(2)
        with fact_col:
            st.markdown("**Fact tables**")
            for tname in ["fact_sales", "fact_shipments", "fact_payments"]:
                schema_df, row_count = get_table_meta(tname)
                with st.expander(f"📊 {tname}  ({row_count:,} rows)"):
                    st.dataframe(schema_df, use_container_width=True, hide_index=True)

        with dim_col:
            st.markdown("**Dimension tables**")
            for tname in ["dim_customer", "dim_product", "dim_warehouse", "dim_date"]:
                schema_df, row_count = get_table_meta(tname)
                with st.expander(f"📋 {tname}  ({row_count:,} rows)"):
                    st.dataframe(schema_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Design Notes")
        st.markdown("""
**Grain**
| Table | One row per |
|---|---|
| `fact_sales` | Sales order line item |
| `fact_shipments` | Shipment record |
| `fact_payments` | Payment record |

**Pre-calculated fields stored in the fact tables**
- `extended_amount` = quantity × unit_price (revenue per line)
- `extended_cost` = quantity × unit_cost (COGS per line)
- `days_to_ship` = shipment_date − order_date
- `days_to_deliver` = delivery_date − shipment_date
- `days_to_pay` = payment_date − invoice_date

**Surrogate key note**
Dimension surrogate keys are currently aligned to the OLTP source IDs (e.g. `customer_key = customer_id`).
This works because the source IDs are stable sequential integers with no reuse.
In a production warehouse, dimension keys would be generated independently to support slowly changing dimensions (SCD) and source-system migrations.
        """)

    # ── Tab 2: OLTP Layer ──────────────────────────────────────────────────────
    with tab_oltp:
        st.markdown(
            "Nine relational tables built across four dependency layers. "
            "Each arrow in the diagram is a foreign key relationship (child → parent)."
        )

        st.plotly_chart(make_oltp_diagram(), use_container_width=True)

        st.divider()
        st.subheader("Row Counts")

        oltp_tables = [
            "customers", "products", "warehouses", "inventory",
            "sales_orders", "sales_order_items", "shipments", "invoices", "payments",
        ]
        # Three columns of metrics (3 per row)
        for row_start in range(0, len(oltp_tables), 3):
            row_tables = oltp_tables[row_start:row_start + 3]
            metric_cols = st.columns(3)
            for col, tname in zip(metric_cols, row_tables):
                _, count = get_table_meta(tname)
                col.metric(tname.replace("_", " "), f"{count:,}")

        st.divider()
        st.subheader("Column Reference")
        st.caption("Expand any table to see its full column list pulled live from the database.")

        layer_groups = {
            "Layer 1 · Foundation (no foreign keys)": ["customers", "products", "warehouses"],
            "Layer 2 · Transactions": ["inventory", "sales_orders"],
            "Layer 3 · Fulfillment":  ["sales_order_items", "shipments", "invoices"],
            "Layer 4 · Collections":  ["payments"],
        }
        for layer_label, tables in layer_groups.items():
            st.markdown(f"**{layer_label}**")
            row_cols = st.columns(len(tables))
            for col, tname in zip(row_cols, tables):
                schema_df, row_count = get_table_meta(tname)
                with col:
                    with st.expander(f"📋 {tname}  ({row_count:,} rows)"):
                        st.dataframe(schema_df, use_container_width=True, hide_index=True)

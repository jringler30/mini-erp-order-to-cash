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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "..", "data", "erp.db")

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
# DATABASE HELPER
# ─────────────────────────────────────────

@st.cache_data
def query(sql):
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql(sql, conn)
    conn.close()
    return df

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="sidebar-title">📦 Mini ERP</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Order-to-Cash Analytics</div>', unsafe_allow_html=True)

    page = st.radio("", [
        "🏠  Executive Overview",
        "📈  Sales Analytics",
        "🚚  Order Operations",
        "🧾  Invoices & Payments",
        "🏭  Inventory Monitoring",
    ])

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

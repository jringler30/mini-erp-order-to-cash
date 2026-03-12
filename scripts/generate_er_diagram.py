# scripts/generate_er_diagram.py
# Generates an ER diagram and saves it to docs/er_diagram.png

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(BASE_DIR, "..", "docs", "er_diagram.png")

fig, ax = plt.subplots(1, 1, figsize=(20, 13))
ax.set_xlim(0, 20)
ax.set_ylim(0, 13)
ax.axis("off")
fig.patch.set_facecolor("#0f1117")
ax.set_facecolor("#0f1117")

# ── Styling ──────────────────────────────
HEADER_COLOR  = "#6366f1"
BOX_COLOR     = "#1a1d27"
BORDER_COLOR  = "#6366f1"
TEXT_COLOR     = "#e0e4f0"
SUB_TEXT_COLOR = "#8b92a5"
LINE_COLOR     = "#6366f1"

def draw_table(ax, x, y, title, fields, width=2.8, row_h=0.32):
    total_h = row_h + len(fields) * row_h
    # Header
    header = FancyBboxPatch((x, y - row_h), width, row_h,
                             boxstyle="round,pad=0.02",
                             facecolor=HEADER_COLOR, edgecolor=BORDER_COLOR, linewidth=1.5)
    ax.add_patch(header)
    ax.text(x + width / 2, y - row_h / 2, title,
            ha="center", va="center", fontsize=9, fontweight="bold",
            color="white", fontfamily="monospace")
    # Field rows
    for i, (fname, ftype) in enumerate(fields):
        row_y = y - row_h - (i + 1) * row_h
        row = FancyBboxPatch((x, row_y), width, row_h,
                              boxstyle="round,pad=0.01",
                              facecolor=BOX_COLOR, edgecolor="#2e3248", linewidth=0.8)
        ax.add_patch(row)
        ax.text(x + 0.12, row_y + row_h / 2, fname,
                ha="left", va="center", fontsize=7.5, color=TEXT_COLOR, fontfamily="monospace")
        ax.text(x + width - 0.12, row_y + row_h / 2, ftype,
                ha="right", va="center", fontsize=7, color=SUB_TEXT_COLOR, fontfamily="monospace")
    return total_h

def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=LINE_COLOR,
                                lw=1.2, connectionstyle="arc3,rad=0.0"))

# ── Table definitions ─────────────────────
tables = {
    "customers": {
        "pos": (0.4, 12.4),
        "fields": [
            ("PK customer_id", "INTEGER"),
            ("customer_name",  "TEXT"),
            ("customer_email", "TEXT"),
            ("region",         "TEXT"),
            ("industry",       "TEXT"),
            ("created_date",   "DATE"),
        ]
    },
    "products": {
        "pos": (8.6, 12.4),
        "fields": [
            ("PK product_id",  "INTEGER"),
            ("sku",            "TEXT"),
            ("product_name",   "TEXT"),
            ("category",       "TEXT"),
            ("unit_cost",      "REAL"),
            ("unit_price",     "REAL"),
            ("active_flag",    "INTEGER"),
        ]
    },
    "warehouses": {
        "pos": (16.6, 12.4),
        "fields": [
            ("PK warehouse_id",   "INTEGER"),
            ("warehouse_name",    "TEXT"),
            ("city",              "TEXT"),
            ("state",             "TEXT"),
        ]
    },
    "inventory": {
        "pos": (16.6, 8.5),
        "fields": [
            ("PK inventory_id",   "INTEGER"),
            ("FK warehouse_id",   "INTEGER"),
            ("FK product_id",     "INTEGER"),
            ("quantity_on_hand",  "INTEGER"),
            ("reorder_point",     "INTEGER"),
            ("last_updated",      "DATE"),
        ]
    },
    "sales_orders": {
        "pos": (0.4, 7.8),
        "fields": [
            ("PK order_id",          "INTEGER"),
            ("FK customer_id",       "INTEGER"),
            ("order_date",           "DATE"),
            ("order_status",         "TEXT"),
            ("requested_ship_date",  "DATE"),
            ("actual_ship_date",     "DATE"),
            ("total_amount",         "REAL"),
        ]
    },
    "sales_order_items": {
        "pos": (8.6, 7.8),
        "fields": [
            ("PK order_item_id", "INTEGER"),
            ("FK order_id",      "INTEGER"),
            ("FK product_id",    "INTEGER"),
            ("quantity",         "INTEGER"),
            ("unit_price",       "REAL"),
            ("line_total",       "REAL"),
        ]
    },
    "shipments": {
        "pos": (0.4, 3.2),
        "fields": [
            ("PK shipment_id",   "INTEGER"),
            ("FK order_id",      "INTEGER"),
            ("FK warehouse_id",  "INTEGER"),
            ("shipment_date",    "DATE"),
            ("delivery_date",    "DATE"),
            ("shipment_status",  "TEXT"),
        ]
    },
    "invoices": {
        "pos": (8.6, 3.8),
        "fields": [
            ("PK invoice_id",    "INTEGER"),
            ("FK order_id",      "INTEGER"),
            ("invoice_date",     "DATE"),
            ("due_date",         "DATE"),
            ("invoice_amount",   "REAL"),
            ("invoice_status",   "TEXT"),
        ]
    },
    "payments": {
        "pos": (8.6, 0.2),
        "fields": [
            ("PK payment_id",    "INTEGER"),
            ("FK invoice_id",    "INTEGER"),
            ("payment_date",     "DATE"),
            ("payment_amount",   "REAL"),
            ("payment_method",   "TEXT"),
        ]
    },
}

# Draw all tables
row_h = 0.32
anchors = {}
for name, data in tables.items():
    x, y = data["pos"]
    fields = data["fields"]
    w = 2.8
    draw_table(ax, x, y, name.upper(), fields, width=w, row_h=row_h)
    mid_x   = x + w / 2
    top_y   = y
    bot_y   = y - row_h - len(fields) * row_h
    right_x = x + w
    left_x  = x
    anchors[name] = {"top": (mid_x, top_y), "bot": (mid_x, bot_y),
                     "left": (left_x, top_y - row_h * 1.5),
                     "right": (right_x, top_y - row_h * 1.5)}

# ── Relationships ─────────────────────────
rels = [
    # customers → sales_orders
    ("customers",       "bot",   "sales_orders",       "top"),
    # sales_orders → sales_order_items
    ("sales_orders",    "right", "sales_order_items",  "left"),
    # products → sales_order_items
    ("products",        "bot",   "sales_order_items",  "top"),
    # products → inventory
    ("products",        "right", "inventory",          "left"),
    # warehouses → inventory
    ("warehouses",      "bot",   "inventory",          "top"),
    # sales_orders → shipments
    ("sales_orders",    "bot",   "shipments",          "top"),
    # warehouses → shipments
    ("warehouses",      "bot",   "shipments",          "right"),
    # sales_orders → invoices
    ("sales_order_items","bot",  "invoices",           "top"),
    # invoices → payments
    ("invoices",        "bot",   "payments",           "top"),
]

for src, src_side, dst, dst_side in rels:
    x1, y1 = anchors[src][src_side]
    x2, y2 = anchors[dst][dst_side]
    arrow(ax, x1, y1, x2, y2)

# ── Title & Legend ────────────────────────
ax.text(10, 0.55, "Mini ERP Order-to-Cash — Entity Relationship Diagram",
        ha="center", va="center", fontsize=13, fontweight="bold",
        color="white", fontfamily="monospace")

legend_elements = [
    mpatches.Patch(facecolor=HEADER_COLOR, label="Table Header"),
    mpatches.Patch(facecolor=BOX_COLOR,    label="Fields"),
    plt.Line2D([0], [0], color=LINE_COLOR, linewidth=1.5, label="Relationship"),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=8,
          facecolor="#1a1d27", edgecolor="#2e3248", labelcolor=TEXT_COLOR)

plt.tight_layout()
plt.savefig(OUT_PATH, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"ER diagram saved to {OUT_PATH}")

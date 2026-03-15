# etl/etl_utils.py
# Shared helpers used by all ETL scripts.
#
# Keeping connection logic and small utilities here means each ETL script
# stays focused on its own job (build schema / load dims / load facts)
# without duplicating boilerplate.

import sqlite3
from pathlib import Path
from datetime import date, timedelta

# ── Paths ──────────────────────────────────────────────────────────────────────
# Both the OLTP tables and the star schema tables live in the same erp.db file.
# Paths are resolved relative to this file so the scripts work on any machine.

BASE_DIR = Path(__file__).resolve().parent.parent   # project root
DB_PATH  = BASE_DIR / "data" / "erp.db"
SQL_DIR  = BASE_DIR / "sql"


# ── Database connection ────────────────────────────────────────────────────────

def get_conn() -> sqlite3.Connection:
    """Open and return a connection to erp.db.

    row_factory = sqlite3.Row makes column access by name possible:
        row["customer_name"]  instead of  row[1]
    which makes ETL code much easier to read and maintain.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Date helpers ───────────────────────────────────────────────────────────────

def date_to_key(date_str) -> int | None:
    """Convert an ISO date string to an integer key in YYYYMMDD format.

    Examples:
        '2024-01-15'            → 20240115
        '2024-01-15 00:00:00'   → 20240115  (timestamp portion is stripped)
        None or ''              → None       (NULL dates stay NULL in facts)

    The integer key format is the standard dim_date primary key convention.
    It keeps joins fast (integer comparison) and readable in SQL WHERE clauses:
        WHERE order_date_key BETWEEN 20240101 AND 20241231
    """
    if not date_str:
        return None
    # Strip any time portion that SQLite may include (e.g. '2024-01-15 00:00:00')
    date_part = str(date_str).split(" ")[0].strip()
    return int(date_part.replace("-", ""))


def daterange(start: date, end: date):
    """Yield every calendar day from start to end, inclusive.

    Used by load_dim_date() to generate one dim_date row per day.
    """
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)

# scripts/create_database.py
# Reads sql/schema.sql and creates the SQLite database at data/erp.db.

import sqlite3
import os

# Build paths relative to this file so the script works on any machine
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(BASE_DIR, "..", "data", "erp.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "..", "sql", "schema.sql")

# Read the schema file
print("Reading schema...")
try:
    with open(SCHEMA_PATH, "r") as f:
        sql = f.read()
    print("Schema loaded.")
except Exception as e:
    print(f"Failed to read schema: {e}")
    exit(1)

# Connect to SQLite (creates erp.db if it doesn't exist)
print("Connecting to database...")
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print(f"Connected to {DB_PATH}")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

# Execute the schema to create all tables
print("Creating tables...")
try:
    cursor.executescript(sql)
    conn.commit()
    print("All tables created successfully.")
except Exception as e:
    print(f"Failed to create tables: {e}")
finally:
    conn.close()
    print("Database connection closed.")

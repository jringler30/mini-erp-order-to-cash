# Claude Memory — Mini ERP Order-to-Cash Project

## Who I'm Working With
- **Name:** Joshua Ringler (GitHub: jringler30)
- **Career:** Heading into ERP consulting — this project is a learning tool to understand ERP systems before starting his job
- **SQL level:** Beginner-to-intermediate. Understands concepts when explained clearly, can write queries with guidance
- **Python level:** Beginner. Not relevant to his job — write Python/Streamlit code for him directly
- **Teaching style:** Guide him through SQL by having him try first, then correct. For everything else (data generation, dashboards, scripts) — just build it

---

## Project Summary

**Repo:** https://github.com/jringler30/mini-erp-order-to-cash
**Deployed:** Streamlit Cloud
**Current version:** v1.0 (tagged on GitHub)
**Working directory:** /Users/joshuaringler/Desktop/ERP System Project

### What Was Built in V1
| File | Purpose |
|---|---|
| `sql/schema.sql` | 9-table relational schema for SQLite |
| `sql/analytics_queries.sql` | 8 business analytics queries |
| `sql/views.sql` | 4 reporting views |
| `scripts/create_database.py` | Builds erp.db from schema.sql |
| `scripts/generate_fake_data.py` | Generates realistic fake ERP data using Faker |
| `scripts/load_data.py` | Inserts data into erp.db, clears tables first in reverse FK order |
| `scripts/generate_er_diagram.py` | Generates docs/er_diagram.png using matplotlib |
| `app/streamlit_app.py` | 5-page dark-themed Streamlit dashboard with Plotly |
| `docs/er_diagram.png` | ER diagram of the 9-table schema |
| `run_project.py` | Entry point stub (not fully implemented) |

### Database Tables (dependency order)
1. `customers`
2. `products`
3. `warehouses`
4. `inventory` (→ products, warehouses)
5. `sales_orders` (→ customers)
6. `sales_order_items` (→ sales_orders, products)
7. `shipments` (→ sales_orders, warehouses)
8. `invoices` (→ sales_orders)
9. `payments` (→ invoices)

### Important Technical Notes
- `erp.db` is in `.gitignore` — NOT in the repo
- Streamlit Cloud deployment auto-builds the database on first launch via `build_database()` in `streamlit_app.py`
- Delete order must be reverse of the above list to respect foreign key constraints
- `strftime('%Y-%m', date)` is how SQLite extracts year-month from a date
- `julianday()` is how SQLite calculates days between two dates

### Dashboard Pages
1. Executive Overview — KPI cards, revenue trend, order status pie
2. Sales Analytics — top products, top customers, revenue by category/region
3. Order Operations — fulfillment KPIs, orders by month, recent orders table
4. Invoices & Payments — invoice status, payment trends, open invoices table
5. Inventory Monitoring — low stock alerts, units by warehouse, full inventory

---

## V2 Ideas (pick these up next session)
- [ ] Returns & refunds module — credit memos, restocking logic
- [ ] PostgreSQL migration — swap SQLite for a real database
- [ ] User authentication — login with role-based access
- [ ] Revenue forecasting — predict next month using historical trends
- [ ] Email alerts — notify when invoices go overdue or inventory hits reorder point
- [ ] CRM module — leads and opportunities feeding into orders
- [ ] `run_project.py` — fully implement as single entry point

---

## Things Joshua Has Learned So Far
- Relational schema design and dependency ordering
- Primary keys, foreign keys, CHECK constraints
- `CREATE TABLE` syntax in SQLite
- `SELECT`, `WHERE`, `GROUP BY`, `ORDER BY`, `SUM()`, `COUNT()`
- JOINs across multiple tables
- `strftime()` and `julianday()` for date math
- `CREATE VIEW` and when views are useful
- Why delete order matters with foreign keys
- `executemany()` and parameterized queries with `?`
- `BASE_DIR` pattern for portable file paths

# Mini ERP Order-to-Cash System with SQL Analytics Dashboard

## Overview
This project simulates a simplified ERP order-to-cash workflow using Python, SQL, SQLite, and Streamlit.

**Workflow:**
`Customer → Sales Order → Order Items → Inventory Check → Shipment → Invoice → Payment`

## Tech Stack
- **Python** — data generation, ETL, and dashboard logic
- **SQL / SQLite** — schema design, queries, views, and analytics
- **Streamlit** — front-end analytics dashboard
- **Pandas** — data loading and table display
- **Plotly** — charts and visualizations

## Project Structure
```
mini-erp-order-to-cash/
├── app/                    # Streamlit dashboard
├── data/                   # SQLite database and sample exports
├── docs/                   # ER diagram, workflow notes, screenshots
├── notebooks/              # Exploratory analysis
├── scripts/                # Database build and data generation scripts
├── sql/                    # Schema, views, and analytics queries
├── requirements.txt
└── run_project.py
```

## Business Questions Answered
- How much revenue did we make?
- Which products sell the most?
- Which customers generate the most revenue?
- Which invoices are unpaid?
- Which products are low in inventory?
- What is the average time from order to payment?

## How to Run Locally
```bash
# 1. Clone the repo
git clone <repo-url>
cd mini-erp-order-to-cash

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build the database
python run_project.py

# 4. Launch the dashboard
streamlit run app/streamlit_app.py
```

## Dashboard Screenshots
_Coming soon_

## Future Improvements
- Migrate from SQLite to PostgreSQL
- Add role-based user interface
- Simulate returns and refunds
- Add CRM lead-to-order module

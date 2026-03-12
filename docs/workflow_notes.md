# ERP Order-to-Cash Workflow Notes

## What is Order-to-Cash?
Order-to-cash (O2C) is the end-to-end business process that starts when a customer places an order and ends when the company receives payment.

## Workflow Steps
1. **Customer** places an order
2. **Sales Order** is created with one or more line items
3. **Inventory** is checked per warehouse
4. **Shipment** is created if items are available
5. **Invoice** is generated after shipment
6. **Payment** is recorded against the invoice

## Table Roles
| Table | Purpose |
|---|---|
| customers | Who is buying |
| products | What is being sold |
| warehouses | Where inventory is held |
| inventory | Stock levels per product per warehouse |
| sales_orders | Order headers |
| sales_order_items | Line items within each order |
| shipments | Fulfillment records |
| invoices | Billing records |
| payments | Payment records against invoices |

## Data Flow
```
customers
    └── sales_orders
            └── sales_order_items ──> products
            └── shipments ──> warehouses ──> inventory
            └── invoices
                    └── payments
```

# Procurement data (DOXA Connex MVP)

This dataset was **provided by Doxa** for the DOXA Connex AI MVP (reports, assistant, and data crawler mock flows).

## Layout

| Folder | Contents |
|--------|----------|
| `raw/` | Original Connex procurement exports (unchanged source files). |
| `expanded/` | Enriched mock datasets (~1,000 rows per table) for LangGraph and backend mocking. |

## Raw source files (`raw/`)

- `purchase_order_202606031055.csv`
- `purchase_req_202606031053.csv`
- `purchase_req_item_202606031054.csv`
- `delivery_order_202606031055.csv`
- `delivery_order_item_202606031056.csv`
- `goods_receipt_202606031056.csv`
- `goods_receipt_item_202606031057.csv`

## Expanded outputs (`expanded/`)

**CSV** (`expanded/csv/`) — normalized domain tables (1,000 rows each):

- `entities.csv`, `vendors.csv`, `projects.csv`
- `purchase_orders.csv`, `invoices.csv`, `payments.csv`
- `contracts.csv`, `approvals.csv`, `alerts_seed.csv`
- `purchase_orders_source_shape.csv`, `purchase_requisitions_source_shape.csv`

**JSON** (`expanded/json/`) — mock API payloads:

- `entities.json`, `vendors.json`, `purchase_orders.json`, `invoices.json`, `payments.json`, `alerts_seed.json`

**Excel** — formatted workbooks with filters and frozen headers:

- `doxa_procurement_mock_expanded.xlsx` (master)
- `doxa_invoices_expanded.xlsx`, `doxa_purchasing_expanded.xlsx`, `doxa_payments_expanded.xlsx`

Do not edit files under `raw/` when refreshing mock data; regenerate or replace content under `expanded/` only.

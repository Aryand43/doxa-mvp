# DOXA MVP

This is the MVP repository for DOXA. Python dependencies and environments are managed using [Poetry](https://python-poetry.org/).

## MVP V1 Demo — "Doxa Connex AI"

A locally runnable, PM-demoable scaffold that shows the three PRD surfaces —
**AI Assistant**, **AI-Generated Reports**, and **AI Data Crawler** — connected
frontend ↔ backend and grounded in the mock procurement data.

### What the scaffold includes

- **Demo orchestration** (`backend/services/orchestrator.py`): heuristic,
  keyword-first router that sends a prompt to the right domain (approvals,
  spend, vendor risk, anomalies, cash flow, contracts, top vendors) or a
  combined **mixed** response. Deterministic — no LLM call required.
- **Grounded procurement service** (`backend/services/procurement.py`): reads
  the mock CSVs and computes committed vs actual spend, pending approvals,
  overdue/anomalous invoices, top vendors, contract expiry, cash-flow ageing,
  and vendor-risk summaries.
- **Report builders** (`backend/services/reports.py`): Spend Analysis, Vendor
  Performance, Cash Flow Forecast, Entity Summary, and On-Demand.
- **Alerts digest** (`backend/services/alerts.py`): prioritised crawler alerts
  with severity, source, description, and recommended action.
- **Retrieval with fallback** (`backend/services/retrieval.py`): uses the IRIS
  vector seam for supporting evidence when available, and **falls back to local
  keyword matching** so the scaffold works with no IRIS and no OpenAI key.
- **One shared response schema** (`backend/services/schema.py`,
  `DemoResponse`): `intent, title, narrative, bullets, metrics, table, alerts,
  actions, evidence, data_scope, confidence` — rendered by a single frontend
  component across all three panels.
- **Demo endpoints** (`backend/routes/demo.py`): `POST /api/demo/query`,
  `POST /api/demo/report`, `GET /api/demo/alerts`, `GET /api/demo/summary`.
- **Polished frontend**: "Doxa Connex AI" shell with a live KPI snapshot bar and
  three wired panels (quick-prompt chips, report-type buttons, alert refresh),
  with loading / empty / error states.

> IRIS fallback: the demo runs fully offline. If IRIS + an OpenAI key are
> configured (see POC 1 below), the Assistant/Reports "evidence" section is
> served by IRIS vector search; otherwise it transparently falls back to local
> text matching. Either way the panels work.

### Run the backend

```bash
poetry install
poetry run uvicorn backend.main:app --reload
```

API at `http://localhost:8000` (docs at `/docs`). The demo endpoints need no
`.env` to function.

### Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed URL (typically `http://localhost:5173`). The Vite dev server
proxies `/api` → `http://localhost:8000`.

### Sample prompts for the PM demo

- What POs are pending my approval today?
- Summarize committed vs actual spend for Project X this month
- Which suppliers have high rejection or risk signals?
- Show invoices with duplicate/fraud/anomaly risk
- Give me a cash flow summary based on invoices and payments
- What contracts are approaching expiry?
- Generate a vendor performance report for a supplier (Reports panel → Vendor
  Performance, e.g. target `GreenBuild`)

## Setup & Installation

### Prerequisites

Ensure you have Python 3.12+ and Poetry installed.

### Install Dependencies

To set up the virtual environment and install all dependencies (including `langgraph`):
```bash
poetry install
```

This will automatically create a virtual environment in a local `.venv/` directory.

## Usage

### Running Commands

To run any script or command within the virtual environment:
```bash
poetry run python your_script.py
```

### Activating the Virtual Environment Shell

To spawn a shell within the virtual environment:
```bash
poetry shell
```

### Managing Dependencies

To add a new package:
```bash
poetry add <package-name>
```

To add a dev dependency:
```bash
poetry add --group dev <package-name>
```

To remove a package:
```bash
poetry remove <package-name>
```

## Backend

The backend is a FastAPI server powered by [LangGraph](https://langchain-ai.github.io/langgraph/) and lives in `backend/`.

### Environment Variables

Copy the example env file and fill in your OpenAI API key:
```bash
cp .env.example .env
```

Edit `.env` and set your key:
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o          # optional, defaults to gpt-4o
```

### Running the Backend

```bash
poetry run uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.
- Health check: `GET /health`
- Chat: `POST /api/chat` with body `{ "message": "...", "session_id": "..." }`

### API Docs

FastAPI auto-generates interactive docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## POC 1 — IRIS Vector DB (procurement vectorization)

The first POC 1 slice vectorizes the **mock `invoices` dataset**
(`data/expanded/csv/invoices.csv`) into an [InterSystems IRIS](https://www.intersystems.com/)
vector table and exposes a retrieval seam for future mock agents. It is
**backend-only** and uses only the mock data already in this repo.

Code layout (`backend/vector/`):
- `embed.py` — text → embeddings (reuses the OpenAI config seam).
- `iris_client.py` — the **only** file with IRIS driver code / vector SQL.
- `ingest.py` — invoices CSV → embedded documents → IRIS.
- `search.py` — `search_procurement_context(query, top_k)`, the agent seam.
- `backend/scripts/index_mock_data.py` — developer CLI (`index` / `query`).

### Required env vars

Add to `.env` (see `.env.example`). Credentials are read from the environment
and never hardcoded:

```
OPENAI_API_KEY=sk-...          # also used for embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536             # MUST match VECTOR(FLOAT, n) in the table

IRIS_HOST=localhost
IRIS_PORT=1972
IRIS_NAMESPACE=USER
IRIS_USERNAME=...              # required
IRIS_PASSWORD=...              # required
IRIS_VECTOR_TABLE=SQLUser.ProcurementVectors
```

### Install the IRIS driver

The driver (`intersystems-irispython`) is declared in `pyproject.toml` and
pinned in `poetry.lock`, so it is installed by the standard:

```bash
poetry install
```

You also need a running IRIS instance with vector search (IRIS 2024.1+),
e.g. the community container:

```bash
docker run -d --name iris -p 1972:1972 -p 52773:52773 \
  -e IRIS_PASSWORD=<your-password> intersystemsdc/iris-community:latest
```

### Index the mock data

```bash
poetry run python -m backend.scripts.index_mock_data index --reset           # all rows
poetry run python -m backend.scripts.index_mock_data index --limit 200       # bound cost
```

### Run a sample retrieval query

```bash
poetry run python -m backend.scripts.index_mock_data query "high risk invoices pending approval"
poetry run python -m backend.scripts.index_mock_data query "overdue payments to GreenBuild" --top-k 3
```

Agents/code can call the seam directly:

```python
from backend.vector import search_procurement_context
matches = search_procurement_context("high risk invoices pending approval", top_k=5)
```

## Frontend

The UI lives in `frontend/` (React, TypeScript, Vite). It is separate from the Python backend and has no API integration yet.

### Setup

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown in the terminal (typically `http://localhost:5173`).
# Doxa Connex AI

A procurement intelligence copilot. One coherent product with three unified
surfaces, all powered by the same backend services, data access layer, and
retrieval engine:

1. **AI Assistant** — natural-language Q&A over procurement data (approvals,
   spend, vendor risk, anomalies, cash flow, contracts).
2. **AI Reports** — structured, grounded reports (Spend Analysis, Vendor
   Performance, Cash Flow Forecast, Entity Summary, On-Demand). Report
   generation is a *mode* of the assistant orchestrator, not a separate engine.
3. **AI Data Crawler** — a real scan over the datasets using deterministic
   detectors + vector retrieval to surface duplicate invoices, anomalous spend,
   price-variance outliers, vendor risk, and contract expiry.

Everything is **grounded in the procurement data in this repo** and runs
**fully offline with zero configuration**. An LLM and InterSystems IRIS are
optional enhancements (see below).

---

## Architecture

```
backend/
  main.py                 # FastAPI app (thin) — mounts routers, CORS, /scalar docs
  config.py               # env config (all optional)
  routes/
    ai.py                 # POST /api/ai/query|report|crawl, GET /api/ai/summary
    health.py             # GET /health
  services/               # thick services — all product logic lives here
    orchestrator.py       # intent classification + routing (single source of truth)
    assistant.py          # Q&A synthesis (gather view + evidence + confidence)
    reports.py            # report-mode builders reusing the same stack
    crawler.py            # deterministic detectors + retrieval + digest
    retrieval.py          # shared semantic retrieval (local vector store / IRIS)
    procurement.py        # domain views -> AIResponse
    schema.py             # shared Pydantic contracts (AIResponse, CrawlResponse)
  data_access/
    loader.py             # load/normalise CSVs (cached)
    queries.py            # reusable filters / aggregations (pandas)
  vector/                 # OPTIONAL IRIS vector seam (embed/ingest/search/client)
  utils/
    text.py               # tokenisation + numeric/money/% formatting
    dates.py              # date parsing + expiry math
    llm.py                # optional LLM explanation (silent fallback)

frontend/src/
  app/                    # App.tsx, api.ts (single typed client), types.ts
  components/             # ResponseCard, MetricStrip, DataTable, AlertList,
                          # PromptChips, Loading/Empty/Error states
  features/
    assistant/            # AssistantPanel
    reports/              # ReportsPanel
    crawler/              # CrawlerPanel
  styles/global.css
```

**Principles applied:** thin routes / thick services, one shared response
schema, one shared retrieval layer, one shared data-access layer, one intent
classifier. Domain logic (`services`, `data_access`) is separate from UI logic
(`frontend`).

---

## Data + Retrieval

- **Source of truth:** the normalised domain datasets in `data/expanded/csv`
  (invoices, payments, purchase_orders, vendors, contracts, approvals, projects,
  entities, alerts_seed). The raw source exports in `data/raw` are not used at
  runtime.
- **`data_access/loader.py`** loads and caches these CSVs; **`queries.py`**
  exposes reusable filters/aggregations.
- **Retrieval (`services/retrieval.py`)** builds a vector index over textual
  records (invoices, contracts, vendors) and ranks them by cosine similarity.
  It is used by the assistant (evidence), reports (evidence), and crawler (related
  records).
  - **Default — local TF-IDF vector store:** built in-process, no external
    services, works fully offline.
  - **Optional — InterSystems IRIS:** set `RETRIEVAL_BACKEND=iris`. If IRIS is
    reachable it is used; on any error it falls back to the local store. Index
    data with `poetry run python -m backend.scripts.index_mock_data index`.

**IRIS is optional.** The product is fully functional without it.

## Crawler

The crawler is a real scan, not an LLM toy. It:
1. loads records from the datasets,
2. runs deterministic detectors,
3. enriches alerts with vector-retrieved related records,
4. optionally adds a plain-language digest via the LLM (if configured),
5. returns a digest + prioritised alerts + scan stats.

Detectors: duplicate invoices (same vendor + amount + retrieval neighbours),
anomalous spend (vs currency/category baseline), price-variance outliers,
vendor risk (HIGH flag + rejection + anomalies), contract expiry (look-ahead
window). Every alert has a severity, plain-language description, the specific
records involved, and a recommended action.

## Optional LLM

Set `OPENAI_API_KEY` to enable natural-language phrasing on top of the
deterministic output. Without it, answers/reports/alerts are still computed
from data — the LLM never invents facts.

---

## Run it

Requires Python 3.12+ and Node 18+.

### Backend

```bash
cp .env.example .env            # optional — defaults work offline
poetry install
poetry run uvicorn backend.main:app --reload
# http://localhost:8000  (API docs at /scalar)
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173  (proxies /api -> backend on :8000)
```

### Tests / build

```bash
cd frontend && npm run test && npm run build
```

---

## API

| Method | Path                   | Purpose                                   |
| ------ | ---------------------- | ----------------------------------------- |
| GET    | `/health`              | Liveness                                  |
| POST   | `/api/ai/query`        | Assistant Q&A (auto-switches to report mode if asked) |
| POST   | `/api/ai/report`       | Structured report (`report_type`, `target`, `prompt`) |
| GET    | `/api/ai/report-types` | Available report types                    |
| POST   | `/api/ai/crawl`        | Data crawler scan (digest + alerts)       |
| GET    | `/api/ai/summary`      | Live KPI snapshot for the header strip    |

`/query` and `/report` return the shared **`AIResponse`**
(`mode, intent, title, narrative, bullets, metrics, table, alerts, actions,
evidence, data_scope, confidence`). `/crawl` returns **`CrawlResponse`**
(`digest, alerts, scan_stats, confidence`).

### Debugging & deployment

- **`/scalar`** — API reference and endpoint mapping (schemas, try-it-out)
- **`/health`** — backend liveness
- **API Inspector** — browser transport log in the frontend (dev by default; set `VITE_ENABLE_API_DEBUG=true` in prod)

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for Vercel setup, env vars, and local vs production flows.

## Example prompts

- What POs are pending my approval today?
- Summarize committed vs actual spend for Project SI-2422
- Which suppliers have the highest rejection or risk signals?
- Show invoices with duplicate/fraud/anomaly risk
- Give me a cash flow summary based on invoices and payments
- What contracts are approaching expiry?
- Generate a vendor performance report for GreenBuild

---

## Removed during cleanup

- `backend/graph/` (LangGraph chatbot/crawler/reporter scaffolding)
- `backend/routes/{chat,crawler,data,demo,reports}.py` (superseded by `ai.py`)
- `backend/llm.py` (moved to `backend/utils/llm.py`)
- `backend/services/{alerts,data_store}.py` (merged into crawler / data_access)
- `frontend/src/App.tsx`, `components/{Card,ResponseView,SummaryBar}.tsx`,
  `features/chat/*`, `features/alerts/*`, `features/reports/ReportPanel.tsx`,
  `lib/{api,session}.ts` (replaced by `app/` + new components/features)

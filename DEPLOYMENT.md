# Deployment

How to deploy **Doxa Connex AI** on Vercel and debug API traffic in the browser.

---

## Recommended structure: two Vercel projects

This monorepo has a Python FastAPI backend at the repo root and a Vite React frontend in `frontend/`. **Two separate Vercel projects** is the cleanest approach:

| Project | Root directory | Runtime | Purpose |
|---------|----------------|---------|---------|
| **doxa-api** | `/` (repo root) | Python / FastAPI | `/health`, `/api/ai/*`, `/scalar`, `/openapi.json` |
| **doxa-web** | `frontend/` | Static (Vite build) | React SPA |

Why two projects?

- Vercel detects FastAPI via `pyproject.toml` → `[tool.vercel]` at the repo root.
- The frontend is a standard Vite static build with its own `package.json`.
- Each surface can scale, redeploy, and roll back independently.
- CORS is explicit between known origins.

A **single Vercel project** is possible but requires custom routing to serve both the Python handler and the SPA from one deployment. That adds complexity without much benefit for this layout — use two projects unless you have a strong reason not to.

---

## Backend (FastAPI on Vercel)

### Entrypoint

Vercel looks for a FastAPI app in default locations. This repo declares it explicitly in `pyproject.toml`:

```toml
[tool.vercel]
entrypoint = "backend.main:app"
```

That points at `backend/main.py`, which exports `app`.

### Deploy steps

1. Create a Vercel project linked to this repo.
2. Set **Root Directory** to `.` (repo root).
3. Vercel auto-detects Python and installs dependencies from `pyproject.toml` / Poetry.
4. Add environment variables (see below).
5. Deploy.

### Backend URLs after deploy

| Path | Purpose |
|------|---------|
| `/health` | Liveness — returns `{"status":"ok"}` |
| `/scalar` | **API reference** — Scalar docs, endpoint schemas, try-it-out |
| `/openapi.json` | OpenAPI spec (used by Scalar) |
| `/api/ai/query` | Assistant Q&A |
| `/api/ai/report` | Structured reports |
| `/api/ai/crawl` | Data crawler scan |
| `/api/ai/summary` | Dashboard KPI snapshot |
| `/api/ai/report-types` | Available report types |

### Backend environment variables (Vercel)

| Variable | Required | Notes |
|----------|----------|-------|
| `OPENAI_API_KEY` | Optional | Enables LLM narratives; app works without it |
| `OPENAI_MODEL` | Optional | Default `gpt-4o` |
| `BACKEND_CORS_ORIGINS` | **Yes in prod** | Comma-separated frontend origins, e.g. `https://doxa-web.vercel.app` |
| `RETRIEVAL_BACKEND` | Optional | `local` (default) or `iris` |
| IRIS vars | Optional | Only if using InterSystems IRIS vector store |

Example:

```env
BACKEND_CORS_ORIGINS=https://doxa-web.vercel.app,https://doxa-web-*.vercel.app
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

---

## Frontend (Vite SPA on Vercel)

### Deploy steps

1. Create a **second** Vercel project linked to the same repo.
2. Set **Root Directory** to `frontend`.
3. **Build Command:** `npm run build` (default)
4. **Output Directory:** `dist` (default for Vite)
5. Add frontend environment variables (see below).
6. Deploy.

For SPA client-side routing, add `frontend/vercel.json`:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### Frontend environment variables (Vercel)

| Variable | Required | Notes |
|----------|----------|-------|
| `VITE_API_BASE_URL` | **Yes in prod** | Backend origin, no trailing slash, e.g. `https://doxa-api.vercel.app` |
| `VITE_ENABLE_API_DEBUG` | Optional | Set `true` to enable API Inspector + console logging in production |

Example:

```env
VITE_API_BASE_URL=https://doxa-api.vercel.app
VITE_ENABLE_API_DEBUG=false
```

Copy `frontend/.env.example` to `frontend/.env.local` for local overrides.

---

## Debugging API traffic

Three complementary tools — each answers a different question:

| Tool | What it shows | When to use |
|------|---------------|-------------|
| **`/scalar`** | API contract — routes, request/response schemas, try-it-out | “What endpoints exist and what shape is the payload?” |
| **`/health`** | Liveness | “Is the backend process up?” |
| **API Inspector** (frontend UI) | Actual browser `fetch` calls — URL, body, status, response, duration | “What did my SPA really send and get back?” |

### Scalar (`/scalar`)

Interactive API reference mounted by FastAPI. Open:

```
https://<your-backend-host>/scalar
```

Use this to explore endpoint mapping and payload contracts. It does **not** show browser-side transport details (CORS preflights, session IDs, etc.).

### API Inspector (frontend dev panel)

Built into the React app. Visible when:

- running `npm run dev` (always on in development), **or**
- `VITE_ENABLE_API_DEBUG=true` in a production build

Click the **API** pill (bottom-right). For each call you see:

- timestamp, method, full URL
- request body, response status, parsed response body
- duration, success/failure

The panel also polls **`/health`** every 30 seconds and shows **Healthy / Unhealthy / Unknown**. A failed health check does not block the app.

Console logging mirrors the same records under `[API]` groups when debug is enabled.

To remove later: delete `ApiInspector.tsx`, `ApiInspector.module.css`, `apiDebug.ts`, and the `<ApiInspector />` import in `App.tsx`.

---

## Local development vs production

### Local (two terminals)

**Backend:**

```bash
cd /path/to/doxa-mvp
poetry install
poetry run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

Local setup:

- `VITE_API_BASE_URL` is **empty** → requests go to same-origin `/api/ai/*` and `/health`.
- Vite proxies `/api` → `http://localhost:8000` (see `frontend/vite.config.ts`).
- API Inspector and console debug logging are **on automatically** in dev.

Optional local env (`frontend/.env.local`):

```env
VITE_API_BASE_URL=
VITE_ENABLE_API_DEBUG=false
```

### Production

- Frontend calls `VITE_API_BASE_URL + /api/ai/...` directly (no Vite proxy).
- Backend must list the frontend origin in `BACKEND_CORS_ORIGINS`.
- Scalar lives on the backend host: `https://<api-host>/scalar`.
- API Inspector is off unless `VITE_ENABLE_API_DEBUG=true`.

---

## Quick verification checklist

After deploying both projects:

1. `curl https://<api-host>/health` → `{"status":"ok"}`
2. Open `https://<api-host>/scalar` → docs load
3. Open frontend URL → live snapshot loads (hits `/api/ai/summary`)
4. Open API Inspector → see the summary request logged
5. Run an assistant query → verify POST `/api/ai/query` in inspector

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Vercel build: “No FastAPI entrypoint found” | Ensure `[tool.vercel] entrypoint = "backend.main:app"` is in `pyproject.toml` |
| CORS errors in browser | Set `BACKEND_CORS_ORIGINS` on backend to your frontend URL |
| Frontend 404 on refresh | Add SPA rewrite in `frontend/vercel.json` |
| API Inspector empty in prod | Set `VITE_ENABLE_API_DEBUG=true` and redeploy frontend |
| Requests go to wrong host | Check `VITE_API_BASE_URL` on frontend project (no trailing slash) |

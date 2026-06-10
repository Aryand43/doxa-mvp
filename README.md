# DOXA MVP

This is the MVP repository for DOXA. Python dependencies and environments are managed using [Poetry](https://python-poetry.org/).

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
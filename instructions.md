# DOXA MVP — IRIS Vector Indexing: End-to-End Guide

This guide walks through running the **IRIS vector indexing POC** end to end:
configure secrets, verify connectivity, index the mock invoices dataset, and
run a sample similarity query.

All credentials are read from `.env` / environment variables only. Nothing is
hardcoded, and no secret values are printed or logged.

---

## 1. Prerequisites

- Python **3.12+** and **Poetry** installed.
- A reachable **InterSystems IRIS** instance with vector search (IRIS 2024.1+).
- An **OpenAI API key** (used for embeddings).

Install backend dependencies (includes the `intersystems-irispython` driver):

```bash
poetry install
```

### Optional: local IRIS via Docker

```bash
docker run -d --name iris -p 1972:1972 -p 52773:52773 \
  -e IRIS_PASSWORD=<your-password> intersystemsdc/iris-community:latest
```

---

## 2. Configure environment

Copy the example file and fill in your own values (this file is git-ignored):

```bash
cp .env.example .env
```

Set these in `.env` (do **not** commit real secrets):

```
OPENAI_API_KEY=sk-...                 # required for embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536                    # MUST match VECTOR(FLOAT, n) in the table

IRIS_HOST=...                         # required
IRIS_PORT=1972                        # required, integer 1-65535
IRIS_NAMESPACE=USER                   # required
IRIS_USERNAME=...                     # required
IRIS_PASSWORD=...                     # required
IRIS_VECTOR_TABLE=SQLUser.ProcurementVectors
```

The OpenAI key may also be supplied purely through the environment instead of
`.env` (e.g. `export OPENAI_API_KEY=...`); the code reads it from either.

---

## 3. Connectivity check (run this first)

Verifies, in order: required env vars are present → IRIS is reachable
(`SELECT 1`) → the target vector table can be checked/created. It fails fast
with clear, secret-free messages and a non-zero exit code if anything is wrong.

```bash
poetry run python -m backend.scripts.index_mock_data check
```

Only report whether the table exists (do not create it):

```bash
poetry run python -m backend.scripts.index_mock_data check --no-create
```

Example healthy output ends with:

```
Result: READY
```

---

## 4. Index the mock invoices dataset

Indexing validates connectivity first (before spending OpenAI tokens), ensures
the table exists, then embeds + **idempotently upserts** rows in batches keyed
on the invoice identifier. Re-running updates rows in place — it does **not**
create duplicates.

```bash
# Index all rows
poetry run python -m backend.scripts.index_mock_data index

# Bound cost while testing
poetry run python -m backend.scripts.index_mock_data index --limit 200

# Drop & recreate the table first (intentional clean slate)
poetry run python -m backend.scripts.index_mock_data index --reset

# Tune batch size (embed + upsert), and add verbose logs
poetry run python -m backend.scripts.index_mock_data -v index --batch-size 50
```

Logs cover each phase: connecting → table check → reading rows → embedding each
batch → upserting each batch → final indexed count read back from IRIS.

---

## 5. Run a sample query

```bash
poetry run python -m backend.scripts.index_mock_data query "high risk invoices pending approval"
poetry run python -m backend.scripts.index_mock_data query "overdue payments to GreenBuild" --top-k 3
```

Programmatic seam (for agents/services):

```python
from backend.vector import search_procurement_context

matches = search_procurement_context("high risk invoices pending approval", top_k=5)
```

---

## 6. Command summary

| Purpose            | Command                                                                          |
| ------------------ | -------------------------------------------------------------------------------- |
| Connectivity check | `poetry run python -m backend.scripts.index_mock_data check`                      |
| Index (all)        | `poetry run python -m backend.scripts.index_mock_data index`                     |
| Index (reset)      | `poetry run python -m backend.scripts.index_mock_data index --reset`             |
| Index (bounded)    | `poetry run python -m backend.scripts.index_mock_data index --limit 200`         |
| Sample query       | `poetry run python -m backend.scripts.index_mock_data query "..." --top-k 5`     |

---

## 7. Troubleshooting

- **`Missing required IRIS settings: ...`** — one or more `IRIS_*` vars are
  empty. Set them in `.env`.
- **`IRIS_PORT must be between 1 and 65535`** — `IRIS_PORT` is missing/invalid.
- **`Could not connect to IRIS ... after 3 attempts`** — host/port unreachable
  or the instance is down. The client retries 3× with linear backoff before
  giving up; check the instance, networking, and firewall.
- **`The 'intersystems-irispython' driver is not installed`** — run
  `poetry install`.
- **Embedding errors / `OPENAI_API_KEY` not set** — set the key; the `check`
  command reports whether it is present.

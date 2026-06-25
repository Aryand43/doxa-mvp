# InterSystems IRIS Vector Search – Quick Guide

This document summarizes how InterSystems IRIS vector search works and how we intend to use it in this project.  
For full details, always refer to the official documentation:

- Using Vector Search in IRIS SQL  
  https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSQL_vecsearch

---

## 1. What vector search is

Vector search represents text (or other unstructured data) as high‑dimensional numeric vectors and ranks stored vectors by semantic similarity to a query vector.  
Similarity is computed with distance functions (for example cosine or dot product), so records with similar meaning appear close to each other in vector space. [file:1]

This is a good fit for retrieval‑augmented generation (RAG), semantic search, and “find similar invoices/contracts/vendors” style tasks.

---

## 2. IRIS vector and embedding types

IRIS SQL adds two key data types for this:

- `VECTOR`: fixed‑length numeric arrays (hundreds or thousands of dimensions) stored as a compact SQL type.
- `EMBEDDING`: a higher‑level type that stores vectors but also knows how to generate them from a source text field using a configured embedding model. [file:1]

You can use these types alongside normal relational columns so a single table can hold both business data and its embeddings.

---

## 3. Populating VECTOR columns

When you manage embeddings yourself (for example using Python + OpenAI or SentenceTransformers), the flow is:

1. Generate embeddings for your text using your chosen model and library.
2. Insert those embeddings into a `VECTOR` column using `TO_VECTOR(...)` in a standard `INSERT` statement. [file:1]

The typical pattern is:

- one column for the embedding,
- one column for a stable identifier that links back to the original text row.

---

## 4. Using EMBEDDING type and configs

Instead of manually generating embeddings, IRIS can do it for you via the `EMBEDDING` type:

1. Create an embedding configuration row in `%Embedding.Config`:
   - `Name`: configuration name (e.g. `my-openai-config`),
   - `Configuration`: JSON with provider‑specific settings (API key, model name, etc.),
   - `EmbeddingClass`: provider implementation (e.g. `%Embedding.OpenAI` or `%Embedding.SentenceTransformers`),
   - `VectorLength`: number of dimensions (for models that require it). [file:1]

2. Define a table with `EMBEDDING` columns, referencing:
   - `model`: the config name from `%Embedding.Config`,
   - `source`: one or more string columns that are converted to embeddings.

On `INSERT`, IRIS will call the configured model, build the embedding, and store it automatically.

---

## 5. Vector indexes (HNSW)

For large datasets, comparing a query vector against every stored vector is expensive. IRIS supports approximate nearest neighbor (ANN) indexes using an HNSW (Hierarchical Navigable Small World) structure. [file:1]

Key points:

- You define an HNSW index on a `VECTOR` or `EMBEDDING` column with `CREATE INDEX ... AS HNSW(...)`.
- The index takes parameters such as:
  - `Distance` (`'Cosine'` or `'DotProduct'`, matching your query function),
  - optional `M` and `efConstruction` to tune recall vs build time. [file:1]
- HNSW indexes are used for queries that include:
  - a `TOP` clause,
  - `ORDER BY ... DESC`,
  - a vector distance expression (for example `VECTOR_COSINE` or `VECTOR_DOT_PRODUCT`). [file:1]

---

## 6. Running vector search queries

Once you have vectors stored (and optionally indexed), you can run vector search with standard SQL:

- Use `VECTOR_DOT_PRODUCT(a, b)` or `VECTOR_COSINE(a, b)` to score similarity.
- Sort by that score in **descending** order and use `TOP N` to get the best matches. [file:1]

Typical pattern:

```sql
SELECT TOP 5 Description
FROM Embedding.Example
ORDER BY VECTOR_DOT_PRODUCT(
  DescriptionEmbedding,
  EMBEDDING(?)
) DESC;
```

Here:

- `DescriptionEmbedding` is an `EMBEDDING` or `VECTOR` column,
- `EMBEDDING(?)` computes the query vector using the same model config bound to that column,
- `?` is supplied from the application as the user’s query text. [file:1]

---

## 7. How we intend to use this in the project

In this codebase, IRIS vector search will be used to:

- store embeddings for invoices, vendors, and contracts,
- expose a `search_procurement_context(query, top_k)` style seam that powers:
  - assistant evidence retrieval,
  - report evidence,
  - crawler “related records” lookups. [file:1]

The plan is:

- embeddings are generated in our Python backend (currently via OpenAI) and written into a `VECTOR` column in IRIS via `TO_VECTOR(...)`,
- an HNSW index is defined on that vector column for fast approximate nearest‑neighbour search,
- all higher‑level services call a single IRIS‑backed search function, not a local TF‑IDF store. [file:1]

For implementation details specific to this repo (table schemas, index scripts, and Python integration), see:

- `docs/iris-vector-setup.md` (this project’s IRIS setup guide),
- `backend/vector/` and `backend/scripts/index_mock_data.py` in the source tree. [file:1]
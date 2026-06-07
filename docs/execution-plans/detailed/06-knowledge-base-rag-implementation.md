# Phase 06 Knowledge Base RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first repair knowledge-base RAG slice with document ingestion, chunk persistence, embeddings, and source-backed retrieval.

**Architecture:** Add a bounded `knowledge_base` module to the API for document/chunk models, chunking, ingestion, retrieval use cases, and repository ports. Keep sqlite as the deterministic local/test store and add PostgreSQL pgvector schema for Docker Compose runtime. The worker owns the Celery embedding task and calls embedding providers through a port so tests use deterministic vectors while later OpenAI-compatible calls stay isolated.

**Tech Stack:** Python, FastAPI, Pydantic, sqlite3, psycopg, PostgreSQL with pgvector, Celery, pytest/httpx, Docker Compose.

---

## Scope Decisions

- Retrieval is a knowledge-base API contract, not an AI answer generator. Phase 06 returns chunks and source metadata only.
- Real LLM/agent workflows, generated replies, diagnostic orchestration, and dispatcher suggestions remain deferred to Phase 07.
- Embedding provider calls stay behind an `EmbeddingProvider` protocol. Tests use deterministic local embeddings.
- The first implementation supports text documents only. PDF parsing, binary uploads, crawling, and object storage are deferred.
- SQLite test retrieval uses deterministic cosine similarity over JSON vectors. PostgreSQL runtime uses pgvector columns and vector distance ordering.
- Source metadata must identify document title, source URI, chunk index, and character offsets for every returned chunk.

## File Responsibility Map

- Create: `apps/api/src/serviceops_api/knowledge_base/__init__.py` for package exports.
- Create: `apps/api/src/serviceops_api/knowledge_base/models.py` for document, chunk, ingest, and retrieval Pydantic models.
- Create: `apps/api/src/serviceops_api/knowledge_base/chunking.py` for deterministic text normalization and overlapping chunk generation.
- Create: `apps/api/src/serviceops_api/knowledge_base/embeddings.py` for `EmbeddingProvider`, deterministic test provider, and vector helpers.
- Create: `apps/api/src/serviceops_api/knowledge_base/repository.py` for sqlite and PostgreSQL knowledge repositories.
- Create: `apps/api/src/serviceops_api/knowledge_base/use_cases.py` for ingest, embedding, and retrieval application services.
- Create: `apps/api/src/serviceops_api/knowledge_base/api.py` for `/knowledge-base/documents` and `/knowledge-base/retrieval` routes.
- Modify: `apps/api/src/serviceops_api/config.py` to add knowledge-base embedding and retrieval settings.
- Modify: `apps/api/src/serviceops_api/main.py` to wire the knowledge-base repository, provider, use cases, and router.
- Create: `apps/api/src/serviceops_api/migrations/0002_knowledge_base_rag.sql` for pgvector extension, document table, chunk table, vector index, and idempotent indexes.
- Create: `apps/api/tests/test_knowledge_base_chunking.py` for chunking behavior.
- Create: `apps/api/tests/test_knowledge_base_api.py` for ingest/retrieval API contracts with deterministic data.
- Modify: `apps/api/tests/test_repository_selection.py` to cover knowledge-base repository selection where needed.
- Modify: `apps/worker/src/serviceops_worker/celery_app.py` to autodiscover/register knowledge-base tasks.
- Create: `apps/worker/src/serviceops_worker/knowledge_base_tasks.py` for `embed_knowledge_document` Celery task.
- Create: `apps/worker/tests/test_knowledge_base_tasks.py` for task registration and provider isolation.
- Modify: `apps/worker/pyproject.toml` if the worker needs `psycopg[binary]` for PostgreSQL embedding writes.
- Modify: `docker-compose.yml` to use a pgvector-capable PostgreSQL image and pass knowledge-base settings into API and worker.
- Modify: `.env.example` to document knowledge-base embedding settings.
- Modify: `domains/knowledge-base/domain.md` to record Phase 06 document, chunk, embedding, retrieval, and source-citation behavior.
- Modify: `docs/harness/repository-map.md` and `tools/repo-checks/check_docs.py` after implementation artifacts exist.
- Modify: `project_notes.md` and `docs/execution-plans/index.md` after implementation to mark Phase 07 active.
- Create: `docs/review/phase-06-review.md` after subagent review.

## Task 1: Chunking And Embedding Ports

**Files:**
- Create: `apps/api/src/serviceops_api/knowledge_base/__init__.py`
- Create: `apps/api/src/serviceops_api/knowledge_base/models.py`
- Create: `apps/api/src/serviceops_api/knowledge_base/chunking.py`
- Create: `apps/api/src/serviceops_api/knowledge_base/embeddings.py`
- Create: `apps/api/tests/test_knowledge_base_chunking.py`

- [ ] **Step 1: Write failing chunking tests**

Create `apps/api/tests/test_knowledge_base_chunking.py` with tests that assert:
- blank document text is rejected by the ingest payload model;
- short text produces one chunk with `chunk_index=0`, `start_char=0`, and `end_char=len(text)`;
- long text produces ordered overlapping chunks;
- deterministic embeddings have a stable dimension and cosine similarity ranks related text above unrelated text.

Run: `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_chunking.py -q`

Expected: fails because the `knowledge_base` package does not exist.

- [ ] **Step 2: Add models**

In `models.py`, add:
- `KnowledgeDocumentStatus = Literal["pending_embedding", "embedded", "failed"]`
- `IngestKnowledgeDocumentPayload` with `title`, optional `source_uri`, `body`, optional `metadata`
- `KnowledgeDocumentResponse`
- `KnowledgeChunkSource`
- `KnowledgeRetrievalPayload`
- `KnowledgeRetrievalResult`
- `KnowledgeRetrievalResponse`

Use Pydantic validators matching existing project style: trim strings, reject empty required fields, cap title at 180 characters, cap body at 100000 characters, cap retrieval query at 2000 characters, and default retrieval `limit` to 5 with range 1..10.

- [ ] **Step 3: Implement chunking**

In `chunking.py`, implement:
- `normalize_text(text: str) -> str`
- `TextChunk` dataclass with `chunk_index`, `content`, `start_char`, `end_char`
- `chunk_text(text: str, max_chars: int = 900, overlap_chars: int = 120) -> list[TextChunk]`

Chunking must be deterministic, preserve character offsets against normalized text, avoid empty chunks, and ensure every chunk after the first starts before the previous chunk ends by `overlap_chars` when possible.

- [ ] **Step 4: Implement embedding helpers**

In `embeddings.py`, add:
- `EmbeddingProvider` protocol with `embed_texts(texts: list[str]) -> list[list[float]]`
- `DeterministicEmbeddingProvider(dimensions: int = 12)`
- `cosine_similarity(left: list[float], right: list[float]) -> float`

The deterministic provider should tokenize lowercased text, hash terms into fixed vector buckets, and normalize vectors for stable tests.

- [ ] **Step 5: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_chunking.py -q`

Expected: passes.

## Task 2: API Repository And Ingestion Contract

**Files:**
- Create: `apps/api/src/serviceops_api/knowledge_base/repository.py`
- Create: `apps/api/src/serviceops_api/knowledge_base/use_cases.py`
- Create: `apps/api/src/serviceops_api/knowledge_base/api.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Create: `apps/api/tests/test_knowledge_base_api.py`

- [ ] **Step 1: Write failing ingest API test**

Create `apps/api/tests/test_knowledge_base_api.py` with an ASGI test that posts to `POST /knowledge-base/documents`:

```json
{
  "title": "E61 group overheating guide",
  "source_uri": "seed://repair/e61-overheating",
  "body": "E61 overheating is often caused by scale in the thermosiphon loop. Descale the group, inspect flow restrictors, and confirm boiler pressure before replacing the pressurestat.",
  "metadata": {"machine_family": "E61"}
}
```

Assert status `201`, document status `embedded`, chunk count greater than zero, and a stable document id.

Run: `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_api.py -q`

Expected: fails because the route does not exist.

- [ ] **Step 2: Implement repository port and sqlite store**

In `repository.py`, add a `KnowledgeBaseStore` protocol and `SqliteKnowledgeBaseRepository` with:
- `initialize()`
- `save_document(title, source_uri, body, metadata, chunks, embeddings) -> dict[str, object]`
- `get_document(document_id: int) -> dict[str, object]`
- `list_chunks_missing_embeddings(document_id: int) -> list[dict[str, object]]`
- `save_chunk_embeddings(document_id: int, embeddings_by_chunk_id: dict[int, list[float]]) -> None`
- `retrieve(query_embedding: list[float], limit: int) -> list[dict[str, object]]`

Use sqlite tables `knowledge_documents` and `knowledge_chunks`. Store metadata and embeddings as JSON text in sqlite.

- [ ] **Step 3: Implement ingest use case**

In `use_cases.py`, add `IngestKnowledgeDocument`. It should validate payload, chunk normalized body, embed chunk contents through the provider, save the document and chunks, and return `KnowledgeDocumentResponse`.

- [ ] **Step 4: Add API router**

In `api.py`, create `create_knowledge_base_router(ingest_document, retrieve_knowledge)`. Wire `POST /knowledge-base/documents` in this task and map repository errors to `404` only where a document lookup is used.

- [ ] **Step 5: Wire `main.py`**

Create the sqlite knowledge repository by default for tests/local direct Python use, instantiate `DeterministicEmbeddingProvider`, wire `IngestKnowledgeDocument`, and include the router.

- [ ] **Step 6: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_api.py -q`

Expected: the ingest test passes.

## Task 3: Retrieval Contract With Source Metadata

**Files:**
- Modify: `apps/api/src/serviceops_api/knowledge_base/use_cases.py`
- Modify: `apps/api/src/serviceops_api/knowledge_base/api.py`
- Modify: `apps/api/tests/test_knowledge_base_api.py`

- [ ] **Step 1: Add failing retrieval tests**

Extend `test_knowledge_base_api.py` to ingest two documents:
- one about E61 overheating, scale, thermosiphon, and boiler pressure;
- one about grinder burr alignment and grind retention.

Post to `POST /knowledge-base/retrieval` with query `"why is my E61 group overheating after descaling"`. Assert:
- status `200`;
- first result references the E61 document;
- every result includes `document_id`, `document_title`, `source_uri`, `chunk_id`, `chunk_index`, `start_char`, `end_char`, `content`, and `score`;
- grinder content is ranked below E61 content or absent when `limit=1`.

Run: `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_api.py -q`

Expected: fails because retrieval is not implemented.

- [ ] **Step 2: Implement retrieval use case**

Add `RetrieveKnowledge` to `use_cases.py`. It should embed the query, call `repository.retrieve()`, and return `KnowledgeRetrievalResponse`.

- [ ] **Step 3: Add retrieval route**

Add `POST /knowledge-base/retrieval` with response model `KnowledgeRetrievalResponse`.

- [ ] **Step 4: Verify**

Run: `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_api.py tests/test_knowledge_base_chunking.py -q`

Expected: passes.

## Task 4: PostgreSQL pgvector Persistence

**Files:**
- Create: `apps/api/src/serviceops_api/migrations/0002_knowledge_base_rag.sql`
- Modify: `apps/api/src/serviceops_api/knowledge_base/repository.py`
- Modify: `apps/api/src/serviceops_api/config.py`
- Modify: `apps/api/src/serviceops_api/main.py`
- Modify: `apps/api/tests/test_repository_selection.py`
- Modify: `docker-compose.yml`
- Modify: `.env.example`

- [ ] **Step 1: Add migration**

Create `0002_knowledge_base_rag.sql` with:
- `CREATE EXTENSION IF NOT EXISTS vector;`
- `knowledge_documents` table with title, source_uri, body, metadata JSONB, status, created_at, and embedded_at;
- `knowledge_chunks` table with document_id, chunk_index, content, start_char, end_char, embedding `vector(12)`, created_at;
- indexes on document status, chunk document id, and a vector index suitable for cosine search.

- [ ] **Step 2: Implement PostgreSQL repository**

Add `PostgresKnowledgeBaseRepository` that normalizes `postgresql+psycopg://` URLs, applies both migration files idempotently, stores metadata as JSONB, stores embeddings as pgvector-compatible literals, and retrieves chunks ordered by vector cosine distance.

- [ ] **Step 3: Add repository factory**

Add `create_knowledge_base_repository(settings, initialize=True)` with sqlite and PostgreSQL branches mirroring the service-request repository selection style.

- [ ] **Step 4: Add config and Compose settings**

Add settings for:
- `knowledge_sqlite_path`
- `knowledge_embedding_dimensions`
- `knowledge_retrieval_limit`

Change Compose PostgreSQL image to a pgvector-capable image and pass database/embedding settings into API and worker. Keep all published ports bound to `127.0.0.1`.

- [ ] **Step 5: Add repository selection tests**

Extend `test_repository_selection.py` to assert PostgreSQL URLs create `PostgresKnowledgeBaseRepository`, sqlite URLs create `SqliteKnowledgeBaseRepository`, and unsupported URLs raise a clear `ValueError`.

- [ ] **Step 6: Verify**

Run:

```bash
cd apps/api && uv run --extra dev pytest tests/test_repository_selection.py tests/test_knowledge_base_api.py -q
docker compose config
```

Expected: both commands pass.

## Task 5: Worker Embedding Job

**Files:**
- Modify: `apps/worker/src/serviceops_worker/celery_app.py`
- Create: `apps/worker/src/serviceops_worker/knowledge_base_tasks.py`
- Modify: `apps/worker/pyproject.toml`
- Create: `apps/worker/tests/test_knowledge_base_tasks.py`

- [ ] **Step 1: Write failing worker tests**

Create `test_knowledge_base_tasks.py` asserting:
- the Celery app registers `serviceops_worker.knowledge_base_tasks.embed_knowledge_document`;
- the task accepts a `document_id`;
- the task uses an embedding provider abstraction and can run with a fake in eager mode without network calls.

Run: `cd apps/worker && uv run --extra dev pytest tests/test_knowledge_base_tasks.py -q`

Expected: fails because the task does not exist.

- [ ] **Step 2: Add task module**

Create `knowledge_base_tasks.py` with:
- `EmbeddingProvider` protocol local to worker or imported through a small duplicated adapter boundary;
- `DeterministicEmbeddingProvider` for local/test execution;
- `embed_knowledge_document(document_id: int) -> dict[str, object]` Celery task.

The task should load missing chunks for the document, embed their content, persist embeddings, and return `{"document_id": document_id, "embedded_chunks": count}`.

- [ ] **Step 3: Register task**

Import/register `serviceops_worker.knowledge_base_tasks` from `create_celery_app()` or configure Celery imports explicitly.

- [ ] **Step 4: Add worker dependencies if needed**

If the task writes directly to PostgreSQL, add `psycopg[binary]>=3.2,<4.0` to worker dependencies and refresh `apps/worker/uv.lock` with `cd apps/worker && uv lock`.

- [ ] **Step 5: Verify**

Run: `cd apps/worker && uv run --extra dev pytest -q`

Expected: passes.

## Task 6: Seed Repair Knowledge Document

**Files:**
- Create: `apps/api/src/serviceops_api/knowledge_base/seed_documents.py`
- Create: `apps/api/tests/test_knowledge_base_seed.py`
- Modify: `apps/api/src/serviceops_api/main.py` only if seed loading is exposed through an explicit local command/helper.

- [ ] **Step 1: Write failing seed test**

Create `test_knowledge_base_seed.py` asserting a seed document exists with:
- title containing `"E61 overheating"`
- source URI `seed://repair/e61-overheating`
- body mentioning thermosiphon, scale, boiler pressure, and pressurestat

Run: `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_seed.py -q`

Expected: fails because the seed module does not exist.

- [ ] **Step 2: Add seed module**

Create `seed_documents.py` with a `REPAIR_KNOWLEDGE_SEED_DOCUMENTS` list of `IngestKnowledgeDocumentPayload` instances. Keep the seed text concise and operationally useful.

- [ ] **Step 3: Verify retrieval against seed**

Add an API test that ingests the seed document and retrieves it for `"E61 overheating pressure"`.

Run: `cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_seed.py tests/test_knowledge_base_api.py -q`

Expected: passes.

## Task 7: Domain Docs, Harness, And Phase Status

**Files:**
- Modify: `domains/knowledge-base/domain.md`
- Modify: `docs/harness/repository-map.md`
- Modify: `tools/repo-checks/check_docs.py`
- Modify: `docs/execution-plans/index.md`
- Modify: `project_notes.md`
- Create: `docs/review/phase-06-review.md`

- [ ] **Step 1: Update knowledge-base domain docs**

Document:
- text document ingestion;
- chunk ordering and source offsets;
- embedding ownership and provider isolation;
- retrieval response source metadata;
- Phase 07 AI workflow boundary.

- [ ] **Step 2: Update repository harness**

Add required Phase 06 artifacts to `tools/repo-checks/check_docs.py` after the files exist:
- detailed Phase 06 plan;
- knowledge-base API module files;
- knowledge-base tests;
- worker task tests;
- Phase 06 review artifact.

Update `docs/harness/repository-map.md` with the new API/worker knowledge-base files.

- [ ] **Step 3: Update phase status**

Update `project_notes.md` to mark Phase 06 complete, Phase 07 active, and record the new decisions. Update `docs/execution-plans/index.md` so active phase is `phases/07-ai-agent-workflows.md` and the detailed Phase 06 plan is listed as completed.

- [ ] **Step 4: Create review artifact**

After implementation and verification, create `docs/review/phase-06-review.md` summarizing:
- files reviewed;
- verification commands and outcomes;
- plan compliance;
- source traceability;
- worker behavior;
- provider isolation;
- final recommendation.

- [ ] **Step 5: Verify docs**

Run: `python3 tools/repo-checks/check_docs.py`

Expected: prints `documentation harness check passed`.

## Task 8: Final Verification

- [ ] Run `cd apps/api && uv run --extra dev pytest`.
- [ ] Run `cd apps/worker && uv run --extra dev pytest`.
- [ ] Run `cd apps/telegram-bot && uv run --extra dev pytest`.
- [ ] Run `npm run web:test`.
- [ ] Run `npm run web:lint`.
- [ ] Run `npm run web:build`.
- [ ] Run `docker compose config`.
- [ ] Run `python3 tools/repo-checks/check_docs.py`.
- [ ] Request subagent review using `docs/review/subagent-review-protocol.md`.
- [ ] Report exact command outcomes and changed files. Do not commit or push unless the user explicitly asks in the current turn.

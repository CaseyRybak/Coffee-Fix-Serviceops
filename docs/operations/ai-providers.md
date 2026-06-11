# AI Provider Operations

ServiceOps supports deterministic local providers and OpenAI-compatible live providers. AI output remains an internal dispatcher-reviewed suggestion. It does not change request status, assign technicians, reserve parts, or notify customers without a staff action.

## Local And Test Mode

Use deterministic providers for local development and automated tests:

```bash
SERVICEOPS_AI_PROVIDER=deterministic
SERVICEOPS_EMBEDDING_PROVIDER=deterministic
SERVICEOPS_KNOWLEDGE_EMBEDDING_DIMENSIONS=1536
```

This mode performs no external network calls and does not require API keys.

## Live Provider Mode

Set these values in Dokploy or a secret store, not in repository files:

```bash
SERVICEOPS_AI_PROVIDER=openai-compatible
SERVICEOPS_AI_MODEL=gpt-4.1-mini
SERVICEOPS_AI_API_BASE_URL=https://api.openai.com/v1
SERVICEOPS_AI_API_KEY=<secret>
SERVICEOPS_AI_TIMEOUT_SECONDS=20
SERVICEOPS_AI_MAX_RETRIES=2

SERVICEOPS_EMBEDDING_PROVIDER=openai-compatible
SERVICEOPS_EMBEDDING_MODEL=text-embedding-3-small
SERVICEOPS_EMBEDDING_API_BASE_URL=https://api.openai.com/v1
SERVICEOPS_EMBEDDING_API_KEY=<secret>
SERVICEOPS_EMBEDDING_TIMEOUT_SECONDS=20
SERVICEOPS_EMBEDDING_MAX_RETRIES=2
```

When a live provider is selected, missing API key or model configuration fails at application startup with a clear configuration error. Deterministic mode remains available without secrets.

For OpenRouter, use the OpenAI-compatible base URL and OpenRouter model slugs:

```bash
SERVICEOPS_AI_API_BASE_URL=https://openrouter.ai/api/v1
SERVICEOPS_AI_MODEL=openai/gpt-4.1-mini
SERVICEOPS_EMBEDDING_API_BASE_URL=https://openrouter.ai/api/v1
SERVICEOPS_EMBEDDING_MODEL=openai/text-embedding-3-small
SERVICEOPS_KNOWLEDGE_EMBEDDING_DIMENSIONS=1536
```

## Provider Contracts

Chat suggestions call `/chat/completions` and request strict JSON with a top-level `suggestions` array. Each suggestion includes `kind`, `title`, `content`, `rationale`, `confidence`, and optional `source_chunk_indexes`.

Embeddings call `/embeddings` with ordered text input and expect one vector per input item. Response vectors are sorted by provider `index` before persistence.

## Privacy And Logging

Provider prompts exclude customer phone numbers, Telegram handles, technician phone numbers, internal note bodies, notification delivery errors, and shared secrets. Provider failures are surfaced as generic `AI provider request failed` or `Embedding provider request failed` messages. Do not log raw prompts, API keys, provider request bodies, provider response bodies, or reusable customer contact data.

## Knowledge Base Content

Curated seed repair documents live in `apps/api/src/serviceops_api/knowledge_base/seed_documents.py`. Each document has a stable `seed://repair/<slug>` source URI and metadata for traceability.

After migrations are applied, ingest the curated repair seed set into the configured database:

```bash
cd apps/api && uv run python -m serviceops_api.operations.seed_knowledge_base
```

The command is idempotent by `source_uri`: rerunning it skips seed documents that are already present.

Run deterministic RAG evaluation through the API test suite:

```bash
cd apps/api && uv run --extra dev pytest tests/test_knowledge_base_seed.py -v
```

The evaluation cases verify that common repair queries retrieve the expected source-backed repair document in the top three results.

## Production Go/No-Go

Before enabling live AI in production:

1. Confirm production uses real provider API keys from a secret store.
2. Run migrations and ingest repair knowledge content.
3. Run deterministic RAG evaluation in CI or local release verification.
4. Perform one dispatcher AI suggestion smoke test on a non-sensitive request.
5. Verify suggestions are visible only in staff dispatcher views.
6. Verify public status responses contain no AI suggestions or provider metadata.

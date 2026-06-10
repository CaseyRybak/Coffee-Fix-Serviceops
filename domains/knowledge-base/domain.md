# Knowledge Base Domain

## Responsibility

This domain manages RAG data for repair knowledge: documents, chunks, embeddings, and retrieval results with sources.

## First Use Cases

- Ingest text document.
- Chunk document.
- Generate embeddings.
- Store vectors in PostgreSQL with pgvector.
- Retrieve relevant chunks for a repair question.

## Phase 06 Behavior

The first implementation accepts text documents through the API and stores normalized chunks with stable ordering and character offsets. Each retrieval result includes the document title, source URI, chunk id, chunk index, offsets, content, and similarity score so later AI workflows can cite their sources instead of using anonymous context.

Embeddings are generated behind an embedding-provider port. Tests and local development use deterministic signed-hash embeddings with a fixed 12-dimension vector, while PostgreSQL runtime stores chunk vectors in pgvector through `knowledge_chunks.embedding`.

The worker owns a Celery task boundary for embedding documents. The task uses repository and embedding-provider protocols so provider calls remain isolated and can be replaced by an OpenAI-compatible adapter in a later slice.

Phase 06 does not generate diagnostic answers, dispatcher suggestions, customer replies, or agent workflow decisions. Those AI workflow behaviors belong to Phase 07 and should consume retrieval results with source metadata.

## Phase 07 Usage

AI workflows can retrieve knowledge chunks for diagnostic and likely-cause suggestions. The retrieved source metadata must remain attached to the AI suggestion so a dispatcher can see which repair document supported the draft.

Knowledge retrieval still returns context only. It does not decide the final diagnosis or create customer-visible content by itself.

## Phase 13 Provider And Content Behavior

Embedding generation remains behind an embedding-provider port. Local development and automated tests use deterministic embeddings, while production can select an OpenAI-compatible embedding provider with secret-backed environment variables.

The seed repair knowledge set now covers common coffee-machine symptoms, brand families, maintenance concepts, intake checklists, and professional pressure/steam triage. Each seed document has a stable `seed://repair/<slug>` source URI and metadata so dispatcher-visible AI suggestions can cite traceable source chunks.

RAG evaluation fixtures exercise representative repair queries and require the expected source-backed document to appear in the top retrieval results. These fixtures are deterministic checks for retrieval usefulness; they do not make claims about live model answer quality.

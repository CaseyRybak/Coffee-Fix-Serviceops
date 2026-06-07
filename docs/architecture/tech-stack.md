# Tech Stack

## Backend

- Python.
- FastAPI.
- Pydantic.
- sqlite3 for deterministic local/test repositories.
- psycopg for PostgreSQL repositories.
- Hand-written SQL migration files applied by repository initialization and the operations migration command.
- pytest.
- httpx.

## Data

- PostgreSQL.
- pgvector.
- Redis.

## Background Work

- Celery with Redis broker for the first implementation.

## AI And RAG

- OpenAI API or compatible LLM provider.
- Custom RAG pipeline before adopting heavier orchestration.
- LangGraph can be introduced when agent workflows need durable state graphs.

## Frontend

- React.
- Vite.
- TypeScript.
- Design based on `reference/figma`.
- lucide-react icons.

## Integrations

- aiogram for Telegram.
- n8n as automation layer.

## Deployment

- Docker Compose.
- VPS.
- Dokploy.
- HTTPS through Dokploy or reverse proxy.

## Deferred Stack Choices

- SQLAlchemy 2.x and Alembic are not part of the current runtime implementation. Revisit them only if the hand-written repository and migration approach becomes too costly to maintain.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN pip install --no-cache-dir "uv>=0.8,<1.0" \
    && uv sync --frozen --no-dev --no-cache

RUN useradd --create-home --shell /usr/sbin/nologin serviceops \
    && chown -R serviceops:serviceops /app

ENV PATH="/app/.venv/bin:$PATH"

USER serviceops

EXPOSE 8000

CMD ["uvicorn", "serviceops_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

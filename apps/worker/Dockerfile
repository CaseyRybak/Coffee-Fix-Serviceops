FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

RUN useradd --create-home --shell /usr/sbin/nologin serviceops \
    && chown -R serviceops:serviceops /app

USER serviceops

CMD ["celery", "-A", "serviceops_worker.celery_app:celery_app", "worker", "--loglevel=INFO"]

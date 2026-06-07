import os

from celery import Celery


def create_celery_app() -> Celery:
    broker_url = os.getenv("SERVICEOPS_REDIS_BROKER_URL", "redis://redis:6379/0")
    result_backend = os.getenv("SERVICEOPS_REDIS_RESULT_BACKEND", "redis://redis:6379/1")

    app = Celery("serviceops-worker", broker=broker_url, backend=result_backend)
    app.conf.update(
        task_default_queue="serviceops",
        task_ignore_result=False,
        imports=("serviceops_worker.knowledge_base_tasks",),
        worker_hijack_root_logger=False,
    )
    app.loader.import_default_modules()
    return app


celery_app = create_celery_app()

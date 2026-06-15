from serviceops_worker.celery_app import create_celery_app


def test_celery_app_uses_serviceops_name_and_redis_defaults() -> None:
    app = create_celery_app()

    assert app.main == "serviceops-worker"
    assert app.conf.broker_url == "redis://redis:6379/0"
    assert app.conf.result_backend == "redis://redis:6379/1"


def test_celery_redis_transport_has_python_client() -> None:
    from kombu.transport import redis as redis_transport

    assert redis_transport.redis.Redis is not None

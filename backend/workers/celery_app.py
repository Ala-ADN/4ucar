"""Celery application factory — broker/backend wired from env."""

from celery import Celery

from backend.shared.config import Settings

_settings = Settings()

celery_app = Celery(
    "ucar",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
    include=[
        "backend.services.ingestion_service.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Tunis",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Route heavy tasks to dedicated queues
    task_routes={
        "backend.services.ingestion_service.tasks.run_extraction": {"queue": "extraction"},
        "backend.services.ingestion_service.tasks.run_ocr_extraction": {"queue": "ocr"},
        "backend.services.ingestion_service.tasks.run_mapping": {"queue": "mapping"},
        "backend.services.ingestion_service.tasks.run_normalization_and_validation": {"queue": "extraction"},
    },
    # Default queue for anything not routed explicitly
    task_default_queue="extraction",
)

"""Celery task worker configuration for Risk2Relief background jobs."""

import logging
from app.core.config import get_settings

logger = logging.getLogger("risk2relief.celery")

settings = get_settings()

try:
    from celery import Celery

    celery_app = Celery(
        "risk2relief_worker",
        broker=settings.get_celery_broker_url(),
        backend=settings.get_celery_result_backend(),
        include=[
            "app.tasks.telemetry_tasks",
            "app.tasks.simulation_tasks",
            "app.tasks.risk_analysis_tasks",
            "app.tasks.anomaly_detection_tasks",
            "app.tasks.report_tasks",
            "app.tasks.maintenance_tasks",
        ]
    )


    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
        worker_prefetch_multiplier=1,
    )
except ImportError:
    celery_app = None
    logger.info("Celery is not installed in current Python environment; worker disabled")

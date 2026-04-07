from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "geo_optimizer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.crawl",
        "app.tasks.monitor",
        "app.tasks.notify",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Beat schedule for monitoring
    beat_schedule={
        "weekly-monitor": {
            "task": "app.tasks.monitor.run_all_monitors",
            "schedule": 604800.0,  # 7 days
        },
    },
)

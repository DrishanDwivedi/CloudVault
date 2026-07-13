from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "cloudvault_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Celery configurations
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # Local Development override
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
)

# Placeholders for celery beat periodic schedules
celery_app.conf.beat_schedule = {
    # We will configure migration checks here in Milestone 6
}

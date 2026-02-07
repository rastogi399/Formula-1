"""
Schumacher - Celery Configuration
Background task processing for DCA, portfolio snapshots, and price updates
"""

from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "solana_copilot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routes
celery_app.conf.task_routes = {
    "app.workers.dca_worker.*": {"queue": "dca"},
    "app.workers.portfolio_worker.*": {"queue": "portfolio"},
    "app.workers.price_worker.*": {"queue": "prices"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Execute DCA automations every minute
    "execute-dca-automations": {
        "task": "app.workers.dca_worker.execute_due_automations",
        "schedule": 60.0,  # Every 60 seconds
    },
    # Update portfolio snapshots every hour
    "update-portfolio-snapshots": {
        "task": "app.workers.portfolio_worker.create_all_snapshots",
        "schedule": 3600.0,  # Every hour
    },
    # Update prices every 30 seconds
    "update-token-prices": {
        "task": "app.workers.price_worker.update_all_prices",
        "schedule": 30.0,  # Every 30 seconds
    },
}

# Import tasks to register them
from app.workers import dca_worker, portfolio_worker, price_worker

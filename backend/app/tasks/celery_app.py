from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "finsight_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.data_sync",
        "app.tasks.model_retrain",
        "app.tasks.model_training",
        "app.tasks.sentiment_pipeline",
        "app.tasks.backtest_resolver",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    # Prevent tasks from running too long
    task_soft_time_limit=1800,   # 30 min soft limit
    task_time_limit=2400,        # 40 min hard kill
    # Worker reliability
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        # ── Phase 1 tasks ──────────────────────────────────────────────────
        # Sync market OHLCV data daily at 4:30pm IST (market close)
        "sync-market-data": {
            "task": "app.tasks.data_sync.sync_all_stocks",
            "schedule": crontab(hour=16, minute=30),
        },
        # Sync broker holdings every 4 hours
        "sync-holdings": {
            "task": "app.tasks.data_sync.sync_all_holdings",
            "schedule": 14400,
        },

        # ── Phase 2 tasks ──────────────────────────────────────────────────
        # Retrain all models weekly on Sunday at 1:00am IST
        # (replaces old "retrain-models" that called model_retrain.retrain_all_models)
        "retrain-all-models": {
            "task": "app.tasks.model_training.retrain_all",
            "schedule": crontab(day_of_week=0, hour=1, minute=0),
        },
        # FinBERT sentiment pipeline — nightly at midnight IST
        "compute-sentiment": {
            "task": "app.tasks.sentiment_pipeline.compute_sentiment_all",
            "schedule": crontab(hour=0, minute=0),
        },
        # Backtest resolver — daily at 6:00am IST (after market data is synced)
        "resolve-predictions": {
            "task": "app.tasks.backtest_resolver.resolve_predictions",
            "schedule": crontab(hour=6, minute=0),
        },
    },
)

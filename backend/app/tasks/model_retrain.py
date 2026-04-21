"""
Legacy shim — kept for backward compatibility with any external callers.
Delegates to app.tasks.model_training.retrain_all.
"""

from app.tasks.celery_app import celery_app
from loguru import logger


@celery_app.task(bind=True, max_retries=1, name="app.tasks.model_retrain.retrain_all_models")
def retrain_all_models(self):
    """Delegate to the Phase 2 bulk retraining task."""
    from app.tasks.model_training import retrain_all
    result = retrain_all.delay()
    logger.info(f"Delegated to retrain_all: task_id={result.id}")
    return {"delegated_task_id": str(result.id)}

#!/bin/bash
cd /Users/rohit/Coding/Finsight_AI/backend
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export TOKENIZERS_PARALLELISM=false
.venv/bin/celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=4

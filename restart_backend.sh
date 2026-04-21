#!/bin/bash
set -e

echo "🔄 Restarting Backend Services..."
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PID_FILE="$ROOT_DIR/.backend.pid"
WORKER_PID_FILE="$ROOT_DIR/.celery_worker.pid"
BEAT_PID_FILE="$ROOT_DIR/.celery_beat.pid"

# Kill existing backend processes
echo "Stopping existing processes..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true

sleep 2

# Start backend
echo "Starting backend..."
mkdir -p "$ROOT_DIR/logs"
cd backend
source .venv/bin/activate

# Backend runs on plain HTTP in dev. Next.js rewrite proxy (undici) does not
# honor NODE_TLS_REJECT_UNAUTHORIZED, so self-signed TLS on the backend breaks
# /api/backend/* with UNABLE_TO_VERIFY_LEAF_SIGNATURE. HTTP on loopback is fine.
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  > ../logs/backend.log 2>&1 &
API_BASE_URL="http://localhost:8000"
BACKEND_PID=$!
echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
echo "✅ Backend started (PID: $BACKEND_PID)"

# Start Celery worker detached.
nohup celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=4 > ../logs/celery_worker.log 2>&1 &
WORKER_PID=$!
echo "$WORKER_PID" > "$WORKER_PID_FILE"
echo "✅ Celery worker started (PID: $WORKER_PID)"

# Start Celery beat detached.
nohup celery -A app.tasks.celery_app beat --loglevel=info > ../logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo "$BEAT_PID" > "$BEAT_PID_FILE"
echo "✅ Celery beat started (PID: $BEAT_PID)"

cd ..

sleep 2

if ! curl -sS -m 5 "$API_BASE_URL/health" >/dev/null 2>&1; then
  echo ""
  echo "❌ Backend health check failed. Recent backend logs:"
  tail -n 40 logs/backend.log
  exit 1
fi

echo ""
echo "✅ All services restarted!"
echo ""
echo "Access points:"
echo "  • Backend API: $API_BASE_URL/docs"
echo "  • Health Check: $API_BASE_URL/health"
echo "  • Frontend: https://localhost:3000"
echo ""
echo "Logs:"
echo "  • Backend: tail -f logs/backend.log"
echo "  • Celery Worker: tail -f logs/celery_worker.log"
echo "  • Celery Beat: tail -f logs/celery_beat.log"
echo ""

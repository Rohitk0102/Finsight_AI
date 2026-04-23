#!/bin/bash

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
BRIGHT_GREEN='\033[1;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'
BOLD='\033[1m'

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
CERTS_DIR="$ROOT_DIR/certs"
LOGS_DIR="$ROOT_DIR/logs"

BACKEND_PID_FILE="$ROOT_DIR/.backend.pid"
FRONTEND_PID_FILE="$ROOT_DIR/.frontend.pid"
WORKER_PID_FILE="$ROOT_DIR/.celery_worker.pid"
BEAT_PID_FILE="$ROOT_DIR/.celery_beat.pid"

mkdir -p "$LOGS_DIR"

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BRIGHT_GREEN}  ┌─────────────────────────────────────────┐${RESET}"
echo -e "${BRIGHT_GREEN}  │        Finsight AI — Manual Start       │${RESET}"
echo -e "${BRIGHT_GREEN}  └─────────────────────────────────────────┘${RESET}"
echo ""

# ── Cleanup on Ctrl+C ────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo -e "${YELLOW}  Shutting down...${RESET}"
  [ -f "$BACKEND_PID_FILE"  ] && kill "$(cat $BACKEND_PID_FILE)"  2>/dev/null && rm -f "$BACKEND_PID_FILE"
  [ -f "$FRONTEND_PID_FILE" ] && kill "$(cat $FRONTEND_PID_FILE)" 2>/dev/null && rm -f "$FRONTEND_PID_FILE"
  [ -f "$WORKER_PID_FILE"   ] && kill "$(cat $WORKER_PID_FILE)"   2>/dev/null && rm -f "$WORKER_PID_FILE"
  [ -f "$BEAT_PID_FILE"     ] && kill "$(cat $BEAT_PID_FILE)"     2>/dev/null && rm -f "$BEAT_PID_FILE"
  
  pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
  pkill -f "celery.*worker" 2>/dev/null || true
  pkill -f "celery.*beat" 2>/dev/null || true
  
  # Kill any child processes attached to this script
  kill 0 2>/dev/null
  echo -e "${GREEN}  Stopped. Goodbye!${RESET}"
  exit 0
}
trap cleanup SIGINT SIGTERM

# ── Check .env ────────────────────────────────────────────────────────────────
if [ ! -f "$ROOT_DIR/.env" ]; then
  if [ -f "$ROOT_DIR/.env.example" ]; then
    echo -e "${YELLOW}  ⚠  .env not found — copying from .env.example${RESET}"
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    echo -e "${RED}  ✗  Fill in your API keys in .env before running again.${RESET}"
    exit 1
  else
    echo -e "${RED}  ✗  No .env file found. Create one first.${RESET}"
    exit 1
  fi
fi
echo -e "${GREEN}  ✓  .env found${RESET}"

# ── Check SSL certificates ────────────────────────────────────────────────────
if [ ! -f "$CERTS_DIR/localhost.crt" ] || [ ! -f "$CERTS_DIR/localhost.key" ]; then
  echo ""
  echo -e "${YELLOW}  ⚠  SSL certificates not found. Generating self-signed certificates...${RESET}"
  mkdir -p "$CERTS_DIR"
  
  openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$CERTS_DIR/localhost.key" \
    -out "$CERTS_DIR/localhost.crt" \
    -days 365 \
    -subj "/C=IN/ST=State/L=City/O=Finsight/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
    2>/dev/null
  
  echo -e "${GREEN}  ✓  SSL certificates generated${RESET}"
  echo -e "${YELLOW}  ⚠  You may need to trust the certificate in your browser${RESET}"
else
  echo -e "${GREEN}  ✓  SSL certificates found${RESET}"
fi

# ── Backend setup ─────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}  ─── Setting up backend...${RESET}"

if [ ! -d "$BACKEND_DIR/.venv" ]; then
  echo -e "${YELLOW}  Creating Python virtual environment...${RESET}"
  python3 -m venv "$BACKEND_DIR/.venv"
fi

source "$BACKEND_DIR/.venv/bin/activate"

# Only install if requirements.txt is newer than a marker file
MARKER_FILE="$BACKEND_DIR/.venv/.deps_installed"
if [ ! -f "$MARKER_FILE" ] || [ "$BACKEND_DIR/requirements.txt" -nt "$MARKER_FILE" ]; then
  echo -e "${YELLOW}  Installing Python dependencies (this may take a minute)...${RESET}"
  pip install -r "$BACKEND_DIR/requirements.txt" --quiet --disable-pip-version-check
  touch "$MARKER_FILE"
  echo -e "${GREEN}  ✓  Python dependencies installed${RESET}"
else
  echo -e "${GREEN}  ✓  Python dependencies up to date (skipping install)${RESET}"
fi

# ── Frontend setup ────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}  ─── Setting up frontend...${RESET}"

# Only install if package.json is newer than node_modules
if [ ! -d "$FRONTEND_DIR/node_modules" ] || [ "$FRONTEND_DIR/package.json" -nt "$FRONTEND_DIR/node_modules" ]; then
  echo -e "${YELLOW}  Installing Node dependencies...${RESET}"
  npm install --prefix "$FRONTEND_DIR" --silent
  echo -e "${GREEN}  ✓  Node dependencies installed${RESET}"
else
  echo -e "${GREEN}  ✓  Node dependencies up to date (skipping install)${RESET}"
fi

# ── Stop existing processes ───────────────────────────────────────────────────
echo ""
echo -e "${CYAN}  ─── Stopping existing processes...${RESET}"

[ -f "$BACKEND_PID_FILE" ] && kill "$(cat "$BACKEND_PID_FILE")" 2>/dev/null && rm -f "$BACKEND_PID_FILE"
[ -f "$FRONTEND_PID_FILE" ] && kill "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null && rm -f "$FRONTEND_PID_FILE"
[ -f "$WORKER_PID_FILE" ] && kill "$(cat "$WORKER_PID_FILE")" 2>/dev/null && rm -f "$WORKER_PID_FILE"
[ -f "$BEAT_PID_FILE" ] && kill "$(cat "$BEAT_PID_FILE")" 2>/dev/null && rm -f "$BEAT_PID_FILE"

pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true

# Check port 8000 (backend)
EXISTING_BACKEND=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$EXISTING_BACKEND" ]; then
  echo -e "${YELLOW}  ⚠  Port 8000 still in use (PID: $EXISTING_BACKEND) — killing it...${RESET}"
  kill -9 $EXISTING_BACKEND 2>/dev/null
  sleep 1
fi

# Check port 3000 (frontend)
EXISTING_FRONTEND=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$EXISTING_FRONTEND" ]; then
  echo -e "${YELLOW}  ⚠  Port 3000 still in use (PID: $EXISTING_FRONTEND) — killing it...${RESET}"
  kill -9 $EXISTING_FRONTEND 2>/dev/null
  sleep 1
fi

echo -e "${GREEN}  ✓  Processes stopped and ports are clear${RESET}"

# ── Load env vars for backend ─────────────────────────────────────────────────
set -a
source "$ROOT_DIR/.env"
if [ -f "$BACKEND_DIR/.env" ]; then
  source "$BACKEND_DIR/.env"
fi
set +a

# ── Start backend on HTTP ─────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}  ─── Starting backend on http://localhost:8000...${RESET}"
cd "$BACKEND_DIR"
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload \
  > "$LOGS_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$BACKEND_PID_FILE"
echo -e "${GREEN}  ✓  Backend started (PID: $BACKEND_PID)${RESET}"

# ── Start Celery Worker ───────────────────────────────────────────────────────
echo -e "${CYAN}  ─── Starting Celery worker...${RESET}"
nohup celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=4 \
  > "$LOGS_DIR/celery_worker.log" 2>&1 &
WORKER_PID=$!
echo "$WORKER_PID" > "$WORKER_PID_FILE"
echo -e "${GREEN}  ✓  Celery worker started (PID: $WORKER_PID)${RESET}"

# ── Start Celery Beat ─────────────────────────────────────────────────────────
echo -e "${CYAN}  ─── Starting Celery beat...${RESET}"
nohup celery -A app.tasks.celery_app beat --loglevel=info \
  > "$LOGS_DIR/celery_beat.log" 2>&1 &
BEAT_PID=$!
echo "$BEAT_PID" > "$BEAT_PID_FILE"
echo -e "${GREEN}  ✓  Celery beat started (PID: $BEAT_PID)${RESET}"

cd "$ROOT_DIR"

# ── Start frontend with HTTPS ─────────────────────────────────────────────────
echo -e "${CYAN}  ─── Starting frontend on https://localhost:3000...${RESET}"
cd "$FRONTEND_DIR"
nohup npm run dev > "$LOGS_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
echo -e "${GREEN}  ✓  Frontend started (PID: $FRONTEND_PID)${RESET}"

cd "$ROOT_DIR"

# ── Wait for services ─────────────────────────────────────────────────────────
echo ""
echo -ne "${YELLOW}  Waiting for services to start...${RESET}"
sleep 4

BACKEND_UP=false
FRONTEND_UP=false

for i in $(seq 1 15); do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    BACKEND_UP=true; break
  fi
  echo -ne "${YELLOW}.${RESET}"
  sleep 1
done

for i in $(seq 1 25); do
  if curl -k -s https://localhost:3000 > /dev/null 2>&1; then
    FRONTEND_UP=true; break
  fi
  echo -ne "${YELLOW}.${RESET}"
  sleep 1
done
echo ""

# ── Status ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BRIGHT_GREEN}  ╔═══════════════════════════════════════════════╗${RESET}"
echo -e "${BRIGHT_GREEN}  ║          Finsight AI is running!              ║${RESET}"
echo -e "${BRIGHT_GREEN}  ╠═══════════════════════════════════════════════╣${RESET}"
echo -e "${BRIGHT_GREEN}  ║                                               ║${RESET}"
if $FRONTEND_UP; then
  echo -e "${BRIGHT_GREEN}  ║  ${GREEN}✓ App:      https://localhost:3000${BRIGHT_GREEN}          ║${RESET}"
else
  echo -e "${BRIGHT_GREEN}  ║  ${YELLOW}⚠ App:      https://localhost:3000 (starting)${BRIGHT_GREEN}║${RESET}"
fi
if $BACKEND_UP; then
  echo -e "${BRIGHT_GREEN}  ║  ${GREEN}✓ API:      http://localhost:8000/api/v1${BRIGHT_GREEN}    ║${RESET}"
  echo -e "${BRIGHT_GREEN}  ║  ${GREEN}✓ API Docs: http://localhost:8000/docs${BRIGHT_GREEN}      ║${RESET}"
else
  echo -e "${BRIGHT_GREEN}  ║  ${YELLOW}⚠ API:      http://localhost:8000 (starting)${BRIGHT_GREEN} ║${RESET}"
fi
echo -e "${BRIGHT_GREEN}  ║                                               ║${RESET}"
echo -e "${BRIGHT_GREEN}  ╚═══════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${YELLOW}Note: You may see a certificate warning in your browser.${RESET}"
echo -e "  ${YELLOW}This is normal for self-signed certificates.${RESET}"
echo -e "  ${YELLOW}Click 'Advanced' → 'Proceed to localhost' to continue.${RESET}"
echo ""
echo -e "  ${CYAN}Logs are being written to:${RESET}"
echo -e "  - logs/backend.log"
echo -e "  - logs/frontend.log"
echo -e "  - logs/celery_worker.log"
echo -e "  - logs/celery_beat.log"
echo ""
echo -e "  ${BOLD}Press Ctrl+C to stop all servers.${RESET}"
echo ""

# ── Tail logs to console ──────────────────────────────────────────────────────
tail -f "$LOGS_DIR/backend.log" "$LOGS_DIR/frontend.log" "$LOGS_DIR/celery_worker.log" "$LOGS_DIR/celery_beat.log" &
TAIL_PID=$!

wait $TAIL_PID

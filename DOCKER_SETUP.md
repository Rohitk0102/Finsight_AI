# Docker Setup Guide

## Issue: Docker Daemon Not Running

The error you're seeing indicates Docker Desktop is not running on your Mac.

```
unable to get image 'finsight_ai-celery_worker': failed to connect to the docker API at unix:///Users/rohit/.docker/run/docker.sock
```

## Solution

### Option 1: Start Docker Desktop (Recommended for Docker)

1. **Open Docker Desktop**
   - Find Docker Desktop in your Applications folder
   - Or use Spotlight: Press `Cmd + Space`, type "Docker", press Enter

2. **Wait for Docker to Start**
   - You'll see the Docker whale icon in your menu bar
   - Wait until it says "Docker Desktop is running"

3. **Run Docker Compose**
   ```bash
   docker-compose up --build
   ```

### Option 2: Run Without Docker (Recommended for Development)

Since you already have everything running locally, Docker is optional. Here's the simpler approach:

#### Terminal 1: Backend
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

#### Terminal 2: Celery Worker
```bash
cd backend
source .venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=4
```

#### Terminal 3: Celery Beat (Optional - for scheduled tasks)
```bash
cd backend
source .venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info
```

#### Terminal 4: Frontend
```bash
cd frontend
npm run dev
```

#### Terminal 5: Redis (if not already running)
```bash
redis-server
```

### Access Points
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Environment Configuration

### For Local Development (No Docker)

**Backend:** Use `backend/.env` with:
```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

**Frontend:** Use `frontend/.env.local` (already configured)

### For Docker

**Root:** Use `.env` with:
```bash
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

The root `.env` file has been updated with:
- ✅ Clerk keys (NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY)
- ✅ Redis URLs for Docker (redis://redis:6379)

## Quick Start Script

I've created a `run.sh` script for easy local development:

```bash
./run.sh
```

This will:
1. Check if services are already running
2. Start backend, Celery worker, and frontend
3. Show you the access URLs

## Troubleshooting

### Issue: Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Issue: Redis Not Running
```bash
# Check if Redis is running
redis-cli ping

# If not, start it
redis-server

# Or on Mac with Homebrew
brew services start redis
```

### Issue: Celery Worker Not Processing Tasks
```bash
# Check Celery worker logs
# Look for "ready" message
# If stuck, restart the worker (Ctrl+C and restart)
```

### Issue: Frontend Build Errors
```bash
cd frontend
rm -rf .next node_modules
npm install
npm run dev
```

## Recommendation

**For development, use Option 2 (local without Docker)** because:
- ✅ Faster startup
- ✅ Easier debugging
- ✅ Hot reload works better
- ✅ No Docker overhead
- ✅ Already working on your machine

**Use Docker only for:**
- Production deployment
- Testing the full containerized stack
- Sharing with team members

## Current Status

Your application is already running locally:
- ✅ Backend: Running (PID 57374)
- ✅ Celery Worker: Running (PID 60925)
- ✅ Celery Beat: Running (PID 57929)
- ✅ Redis: Running
- ✅ ML Models: 28 tickers trained

**You don't need Docker right now!** Just start the frontend:

```bash
cd frontend && npm run dev
```

Then access: http://localhost:3000

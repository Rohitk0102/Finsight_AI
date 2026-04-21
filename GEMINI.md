# Finsight AI - Project Guidelines

## Project Overview
Finsight AI is a comprehensive, AI-powered stock market prediction and portfolio management platform. It combines machine learning models with real-time market data to provide actionable financial insights.

### Architecture
- **Backend:** FastAPI (Python) handles the API, authentication (via Clerk), and business logic.
- **Frontend:** Next.js (React/TypeScript) provides a responsive, themed UI.
- **Task Queue:** Celery with Redis manages background data fetching and ML inference.
- **Database:** Supabase (PostgreSQL) for persistent data storage.
- **ML Engine:** Integrated models using LSTM, Prophet, and XGBoost for stock price predictions and sentiment analysis.
- **Infrastructure:** Docker and Nginx for containerization and SSL termination.

## Building and Running

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- Redis Server
- Supabase Account (for DB)
- Clerk Account (for Auth)

### Key Commands

**Local Development:**
```bash
# Backend (from ./backend)
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Celery Worker (from ./backend)
celery -A app.tasks.celery_app worker --loglevel=info

# Frontend (from ./frontend)
npm install
npm run dev
```

**System Health Check:**
```bash
./test_system.sh
```

**Docker Deployment:**
```bash
docker-compose up --build
```

## Development Conventions

### Backend (FastAPI)
- **Modularity:** Follow the existing structure: `api/routes/` for endpoints, `services/` for business logic, and `schemas/` for Pydantic models.
- **Middleware:** Use `backend/app/api/middleware.py` for cross-cutting concerns like logging and performance monitoring.
- **Authentication:** Use the `get_current_user` dependency in routes to enforce Clerk-based authentication.
- **Persistence:** Use the Supabase client defined in `core/supabase.py`. Enforce authorization logic at the API level as RLS is bypassed via service-role keys.

### Frontend (Next.js)
- **Auth Middleware:** Ensure `frontend/middleware.ts` is correctly configured to inject Clerk JWTs into proxied backend requests.
- **API Client:** Use the `apiClient` in `frontend/lib/api/client.ts` for all backend communication to ensure consistent token handling and error management.
- **Styling:** Use TailwindCSS and adhere to the established dark/light theme system.
- **Components:** Modularize UI elements within `frontend/components/` and use Radix UI primitives for accessible components.

### Database Migrations
- SQL migrations are located in `supabase/migrations/`. 
- **CRITICAL:** Always verify and apply migrations via the Supabase SQL editor as part of phase updates.

### Code Quality
- **Type Safety:** Maintain strict TypeScript typing in the frontend and Pydantic validation in the backend.
- **Logging:** Use `loguru` in the backend for structured, informative logging.
- **Testing:** Add or update tests in `backend/tests/` and `frontend/**/*.test.tsx` for new features or bug fixes.

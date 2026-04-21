import warnings
import os

# Ultra-aggressive warning suppression before any other imports
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore", message=".*Pandas4Warning.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import time
import httpx
import re

from app.core.config import settings
from app.core.redis import get_redis, close_redis
from app.api.routes import auth, stocks, predict, news, portfolio, broker, screener, markets
from app.api.middleware import LoggingMiddleware, ProcessTimeMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await get_redis()  # warm up connection pool
    yield
    # Shutdown
    await close_redis()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered stock market prediction and portfolio management platform",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
localhost_origin_regex = (
    r"https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    if settings.ENVIRONMENT != "production"
    else None
)
localhost_origin_pattern = re.compile(localhost_origin_regex) if localhost_origin_regex else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=localhost_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(ProcessTimeMiddleware)

logger.info(f"CORS allow_origins={settings.ALLOWED_ORIGINS} allow_origin_regex={localhost_origin_regex}")


def _get_allowed_origin(request: Request) -> str | None:
    origin = request.headers.get("origin")
    if not origin:
        return None
    if origin in settings.ALLOWED_ORIGINS:
        return origin
    if localhost_origin_pattern and localhost_origin_pattern.fullmatch(origin):
        return origin
    return None


def _attach_cors_headers(request: Request, response: JSONResponse) -> JSONResponse:
    origin = _get_allowed_origin(request)
    if not origin:
        return response
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Vary"] = "Origin"
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url}: {exc}")
    message = str(exc).lower()
    is_connectivity_error = isinstance(exc, httpx.HTTPError) or any(
        marker in message
        for marker in (
            "nodename nor servname provided",
            "name or service not known",
            "temporary failure in name resolution",
            "connection refused",
            "timed out",
        )
    )
    if is_connectivity_error:
        return _attach_cors_headers(request, JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Upstream service unavailable. Check SUPABASE_URL/network and retry."},
        ))
    return _attach_cors_headers(request, JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    ))


# ── Routes ────────────────────────────────────────────────────────────────────
PREFIX = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=PREFIX)
app.include_router(stocks.router, prefix=PREFIX)
app.include_router(predict.router, prefix=PREFIX)
app.include_router(news.router, prefix=PREFIX)
app.include_router(portfolio.router, prefix=PREFIX)
app.include_router(broker.router, prefix=PREFIX)
app.include_router(screener.router, prefix=PREFIX)
app.include_router(markets.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}

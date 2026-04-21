import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        try:
            response = await call_next(request)
            logger.info(f"Response: {response.status_code} for {request.method} {request.url}")
            return response
        except Exception as e:
            logger.error(f"Request failed: {request.method} {request.url} - Error: {e}")
            raise e

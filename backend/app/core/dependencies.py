from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_clerk_token
from app.core.redis import get_redis
from app.core.config import settings
from loguru import logger

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Validate Clerk JWT and return user payload."""
    token = credentials.credentials
    try:
        payload = await verify_clerk_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing sub")
        return {
            "id": user_id,                        # Clerk user ID, e.g. user_2abc123
            "email": payload.get("email", ""),
            "token": token,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> dict | None:
    """Same as get_current_user but returns None instead of raising if unauthenticated."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def rate_limit(
    request_ip: str,
    endpoint: str,
    limit: int = settings.RATE_LIMIT_REQUESTS,
    window: int = settings.RATE_LIMIT_WINDOW_SECONDS,
):
    """Sliding window rate limiter using Redis."""
    r = await get_redis()
    real_ip = request_ip
    if request_ip in ["127.0.0.1", "localhost"]:
        real_ip = "dev_client"
    key = f"ratelimit:{real_ip}:{endpoint}"
    current = await r.incr(key)
    if current == 1:
        await r.expire(key, window)
    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {limit} requests per {window}s.",
        )

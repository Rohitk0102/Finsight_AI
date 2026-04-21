"""
Broker OAuth callback routes.
Each broker has its own OAuth flow — this file handles the redirect URIs.
"""
import asyncio
import httpx
from fastapi import APIRouter, Query, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from app.core.dependencies import get_current_user
from app.core.supabase import supabase
from app.core.security import encrypt_token
from app.core.config import settings
from app.services.broker.upstox_broker import UpstoxBroker
from app.services.broker.zerodha_broker import ZerodhaBroker
from app.services.broker.angelone_broker import AngelOneBroker
from loguru import logger

router = APIRouter(prefix="/broker", tags=["broker"])


def _is_connectivity_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPError):
        return True
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "nodename nor servname provided",
            "name or service not known",
            "temporary failure in name resolution",
            "connection refused",
            "timed out",
        )
    )


async def _execute_query(query, *, operation: str):
    try:
        return await asyncio.to_thread(query.execute)
    except Exception as exc:
        if _is_connectivity_error(exc):
            logger.error(f"{operation} failed due to DB connectivity: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable. Check SUPABASE_URL/network and retry.",
            )
        logger.error(f"{operation} failed: {exc}")
        raise HTTPException(status_code=500, detail=f"{operation} failed")


# ── Upstox OAuth ──────────────────────────────────────────────────────────────

@router.get("/upstox/authorize")
async def upstox_authorize(current_user: dict = Depends(get_current_user)):
    """Redirect user to Upstox OAuth page."""
    broker = UpstoxBroker()
    # Use user ID as state parameter for security
    auth_url = broker.get_auth_url() + f"&state={current_user['id']}"
    return {"auth_url": auth_url}


@router.get("/upstox/callback")
async def upstox_callback(
    code: str = Query(...),
    state: str = Query(...),  # Make state required
    request: Request = None,
):
    try:
        # Validate state parameter exists and is a valid UUID
        if not state or len(state) != 36:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
            
        broker = UpstoxBroker()
        token_data = await broker.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        profile = await broker.get_profile(access_token)

        # Store encrypted token using validated user_id from state
        await _execute_query(
            supabase.table("broker_accounts").upsert(
                {
                    "user_id": state,  # state param carries user_id
                    "broker": "upstox",
                    "account_id": profile.get("client_id"),
                    "display_name": profile.get("name"),
                    "access_token_encrypted": encrypt_token(access_token),
                    "is_active": True,
                },
                on_conflict="user_id,broker",
            ),
            operation="broker_upstox_upsert",
        )

        frontend_url = settings.FRONTEND_APP_URL.rstrip("/")
        return RedirectResponse(url=f"{frontend_url}/settings?connected=upstox")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upstox callback error: {e}")
        raise HTTPException(status_code=400, detail="Upstox authorization failed")


# ── Zerodha Kite ──────────────────────────────────────────────────────────────

@router.post("/zerodha/connect")
async def zerodha_connect(
    request_token: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Zerodha uses a request_token flow (not standard OAuth redirect).
    Frontend redirects to Kite login, captures request_token, sends here.
    """
    try:
        broker = ZerodhaBroker()
        session = await broker.generate_session(request_token)
        access_token = session["access_token"]
        profile = await broker.get_profile(access_token)

        await _execute_query(
            supabase.table("broker_accounts").upsert(
                {
                    "user_id": current_user["id"],
                    "broker": "zerodha",
                    "account_id": profile.get("user_id"),
                    "display_name": profile.get("user_name"),
                    "api_key": settings.ZERODHA_API_KEY,
                    "access_token_encrypted": encrypt_token(access_token),
                    "is_active": True,
                },
                on_conflict="user_id,broker",
            ),
            operation="broker_zerodha_upsert",
        )

        return {"message": "Zerodha connected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Zerodha connect error: {e}")
        raise HTTPException(status_code=400, detail="Zerodha connection failed")


# ── Angel One ─────────────────────────────────────────────────────────────────

@router.post("/angelone/connect")
async def angelone_connect(
    client_id: str,
    mpin: str,
    totp: str,
    current_user: dict = Depends(get_current_user),
):
    """Angel One uses MPIN + TOTP authentication (no OAuth redirect)."""
    try:
        broker = AngelOneBroker()
        session = await broker.login(client_id, mpin, totp)
        access_token = session["jwtToken"]
        profile = session.get("data", {})

        await _execute_query(
            supabase.table("broker_accounts").upsert(
                {
                    "user_id": current_user["id"],
                    "broker": "angel_one",
                    "account_id": client_id,
                    "display_name": profile.get("name", client_id),
                    "access_token_encrypted": encrypt_token(access_token),
                    "is_active": True,
                },
                on_conflict="user_id,broker",
            ),
            operation="broker_angelone_upsert",
        )

        return {"message": "Angel One connected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Angel One connect error: {e}")
        raise HTTPException(status_code=400, detail="Angel One connection failed")

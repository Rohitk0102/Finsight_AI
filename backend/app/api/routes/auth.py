import asyncio
import httpx
import uuid
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.user import UserProfile, UserProfileUpdate
from app.core.supabase import supabase
from app.core.dependencies import get_current_user
from loguru import logger

router = APIRouter(prefix="/auth", tags=["auth"])

# Signup, login, logout, and token refresh are handled entirely by Clerk on the
# frontend. The backend only needs to manage user profile data in the database.


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


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the profile row for the authenticated Clerk user."""
    result = await _execute_query(
        supabase.table("user_profiles")
        .select("*")
        .eq("clerk_id", current_user["id"])
        .single(),
        operation="auth_profile_fetch",
    )
    if not result.data:
        # Auto-create a profile on first access
        new_profile = {
            "clerk_id": current_user["id"],
            "email": current_user.get("email", ""),
        }
        insert_result = await _execute_query(
            supabase.table("user_profiles").insert(new_profile),
            operation="auth_profile_create",
        )
        if not insert_result.data:
            raise HTTPException(status_code=500, detail="Failed to create user profile")
        return insert_result.data[0]
    return result.data


@router.patch("/me")
async def update_profile(
    payload: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update the profile for the authenticated Clerk user."""
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await _execute_query(
        supabase.table("user_profiles")
        .update(update_data)
        .eq("clerk_id", current_user["id"]),
        operation="auth_profile_update",
    )
    return result.data[0] if result.data else {}

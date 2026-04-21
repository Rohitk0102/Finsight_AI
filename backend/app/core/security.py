import time
import httpx
from jose import jwt, JWTError
from cryptography.fernet import Fernet
import base64

from app.core.config import settings

# ── Clerk JWKS verification ───────────────────────────────────────────────────

_jwks_cache: dict = {"keys": [], "fetched_at": 0.0}
_JWKS_TTL = 3600  # re-fetch keys at most once per hour


async def _get_clerk_jwks() -> list:
    global _jwks_cache
    now = time.time()
    if _jwks_cache["keys"] and now - _jwks_cache["fetched_at"] < _JWKS_TTL:
        return _jwks_cache["keys"]
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(settings.CLERK_JWKS_URL)
        resp.raise_for_status()
    keys = resp.json().get("keys", [])
    _jwks_cache = {"keys": keys, "fetched_at": now}
    return keys


async def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk-issued JWT using the published JWKS.
    Returns the decoded payload on success; raises JWTError on failure.
    """
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")

    keys = await _get_clerk_jwks()
    rsa_key = next((k for k in keys if k.get("kid") == kid), None)

    if rsa_key is None:
        # Key not found — force a cache refresh once in case Clerk rotated keys
        _jwks_cache["fetched_at"] = 0.0
        keys = await _get_clerk_jwks()
        rsa_key = next((k for k in keys if k.get("kid") == kid), None)

    if rsa_key is None:
        raise JWTError("No matching key found in Clerk JWKS")

    payload = jwt.decode(
        token,
        rsa_key,
        algorithms=["RS256"],
        options={"verify_aud": False},  # Clerk tokens don't always set aud
    )
    return payload


# ── Broker token encryption (AES-256 via Fernet) ─────────────────────────────

def _get_fernet() -> Fernet:
    key = settings.BROKER_TOKEN_ENCRYPTION_KEY
    key_bytes = base64.urlsafe_b64decode(key.encode())
    assert len(key_bytes) == 32, "BROKER_TOKEN_ENCRYPTION_KEY must be 32 bytes base64-encoded"
    return Fernet(key.encode())


def encrypt_token(plain_text: str) -> str:
    return _get_fernet().encrypt(plain_text.encode()).decode()


def decrypt_token(cipher_text: str) -> str:
    return _get_fernet().decrypt(cipher_text.encode()).decode()

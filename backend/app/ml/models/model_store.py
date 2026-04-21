"""
Versioned model registry.

Directory layout:
  ml_models/
    lstm/{ticker}/v{n}.pt
    lstm/{ticker}/v{n}_scaler.pkl
    lstm/{ticker}/metadata.json
    prophet/{ticker}/v{n}.pkl
    prophet/{ticker}/metadata.json
    xgb/{ticker}/v{n}.pkl
    xgb/{ticker}/metadata.json

metadata.json fields:
  version, trained_at (ISO UTC), features_used, mape, n_samples
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

MODEL_ROOT = Path(__file__).parent.parent.parent.parent.parent / "ml_models"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _ticker_dir(model_type: str, ticker: str) -> Path:
    d = MODEL_ROOT / model_type / ticker
    d.mkdir(parents=True, exist_ok=True)
    return d


def _meta_path(model_type: str, ticker: str) -> Path:
    return MODEL_ROOT / model_type / ticker / "metadata.json"


# ── Public API ────────────────────────────────────────────────────────────────

def load_metadata(model_type: str, ticker: str) -> Optional[dict]:
    """Return parsed metadata.json or None if absent."""
    p = _meta_path(model_type, ticker)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def save_metadata(model_type: str, ticker: str, meta: dict) -> None:
    p = _meta_path(model_type, ticker)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(meta, indent=2, default=str))


def model_file(model_type: str, ticker: str, suffix: str) -> Path:
    """
    Return the path to the current versioned model artefact.

    Examples:
      model_file("lstm",    "AAPL", ".pt")           → ml_models/lstm/AAPL/v2.pt
      model_file("lstm",    "AAPL", "_scaler.pkl")   → ml_models/lstm/AAPL/v2_scaler.pkl
      model_file("xgb",     "AAPL", ".pkl")          → ml_models/xgb/AAPL/v1.pkl
      model_file("prophet", "AAPL", ".pkl")          → ml_models/prophet/AAPL/v1.pkl
    """
    meta = load_metadata(model_type, ticker)
    version = meta["version"] if meta else "v1"
    return _ticker_dir(model_type, ticker) / f"{version}{suffix}"


def next_version_tag(model_type: str, ticker: str) -> str:
    """Return the *next* version string (before saving new artefact)."""
    meta = load_metadata(model_type, ticker)
    if not meta:
        return "v1"
    try:
        n = int(meta["version"].lstrip("v"))
        return f"v{n + 1}"
    except (KeyError, ValueError):
        return "v1"


def get_model_version(model_type: str, ticker: str) -> str:
    meta = load_metadata(model_type, ticker)
    return meta["version"] if meta else "unknown"


def needs_training(model_type: str, ticker: str, max_age_hours: float = 24.0) -> bool:
    """Return True when the model is absent or older than *max_age_hours*."""
    meta = load_metadata(model_type, ticker)
    if not meta or "trained_at" not in meta:
        return True
    try:
        trained_at = datetime.fromisoformat(meta["trained_at"])
        if trained_at.tzinfo is None:
            trained_at = trained_at.replace(tzinfo=timezone.utc)
        age_h = (datetime.now(timezone.utc) - trained_at).total_seconds() / 3600.0
        return age_h > max_age_hours
    except Exception:
        return True


def composite_version(ticker: str) -> str:
    """Combine model versions for all three models into one version string."""
    parts = []
    for mt in ("xgb", "lstm", "prophet"):
        parts.append(f"{mt}:{get_model_version(mt, ticker)}")
    return "|".join(parts)

"""
Offline LSTM trainer — called exclusively by Celery tasks, never in the API path.

Trains a 2-layer LSTM with:
  - All technical indicator features (LSTM_FEATURE_COLS)
  - StandardScaler per-feature and per-target
  - 85/15 train/val split with early-stopping via best-val tracking
  - HuberLoss + gradient clipping + ReduceLROnPlateau
  - 200 epochs

Artefacts saved to: ml_models/lstm/{ticker}/
  {version}.pt            — best model state_dict
  {version}_scaler.pkl    — {"scaler_X": ..., "scaler_y": ..., "features": [...]}
  metadata.json           — version, trained_at, mape, features_used, n_samples
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
import joblib
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from app.ml.utils.feature_engineering import compute_features, LSTM_FEATURE_COLS
from app.ml.models.model_store import (
    _ticker_dir,
    save_metadata,
    next_version_tag,
    needs_training,
)

SEQ_LEN = 60
EPOCHS = 200
HIDDEN = 128
LAYERS = 2
DROPOUT = 0.3
FORWARD_DAYS = 7  # LSTM predicts 7-day ahead price


# ── Model architecture (shared between trainer and ensemble) ──────────────────

def build_lstm(n_features: int):
    """Return an uninitialised LSTMNet. Import torch lazily."""
    import torch.nn as nn

    class LSTMNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(
                n_features, HIDDEN, LAYERS,
                batch_first=True, dropout=DROPOUT,
            )
            self.dropout = nn.Dropout(0.2)
            self.fc = nn.Linear(HIDDEN, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(self.dropout(out[:, -1, :]))

    return LSTMNet()


# ── Public entry point ────────────────────────────────────────────────────────

def train_lstm(ticker: str, force: bool = False) -> Optional[dict]:
    """
    Train LSTM for *ticker*, persist artefacts, return metadata dict.
    Returns None when training is skipped (model is fresh).
    Raises on irrecoverable errors so the Celery task can handle retries.
    """
    if not force and not needs_training("lstm", ticker):
        logger.info(
            "LSTM skipped (fresh model)",
            extra={"ticker": ticker, "action": "skip_train"},
        )
        return None

    try:
        import torch
        import torch.nn as nn
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise RuntimeError(f"Missing ML dependency: {exc}") from exc

    # ── Fetch data ────────────────────────────────────────────────────────────
    t = yf.Ticker(ticker)
    df = t.history(period="3y", interval="1d")
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    if len(df) < SEQ_LEN + 80:
        raise ValueError(f"Insufficient data for {ticker}: {len(df)} rows")

    featured = compute_features(df)
    available = [c for c in LSTM_FEATURE_COLS if c in featured.columns]
    if len(available) < 8:
        raise ValueError(f"Too few features ({len(available)}) for {ticker}")

    feat_matrix = featured[available].values.astype(np.float32)
    close_vals = featured["Close"].values.astype(np.float32)

    # ── Normalise ─────────────────────────────────────────────────────────────
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    feat_scaled = scaler_X.fit_transform(feat_matrix)
    close_scaled = scaler_y.fit_transform(close_vals.reshape(-1, 1)).ravel()

    # ── Build sequences ───────────────────────────────────────────────────────
    X_list, y_list = [], []
    for i in range(SEQ_LEN, len(feat_scaled) - FORWARD_DAYS):
        X_list.append(feat_scaled[i - SEQ_LEN : i])
        y_list.append(close_scaled[i + FORWARD_DAYS - 1])

    if len(X_list) < 60:
        raise ValueError(f"Not enough sequences ({len(X_list)}) for {ticker}")

    X = torch.tensor(np.array(X_list), dtype=torch.float32)
    y = torch.tensor(np.array(y_list), dtype=torch.float32).unsqueeze(-1)

    split = int(len(X) * 0.85)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    # ── Train ─────────────────────────────────────────────────────────────────
    model = build_lstm(len(available))
    optimizer = torch.optim.Adam(model.parameters(), lr=5e-4, weight_decay=1e-5)
    criterion = nn.HuberLoss()
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=15, factor=0.5, min_lr=1e-6,
    )

    best_val_loss = float("inf")
    best_state: dict = {}
    patience_counter = 0
    EARLY_STOP_PATIENCE = 30  # stop if no improvement for 30 epochs

    for epoch in range(EPOCHS):
        model.train()
        optimizer.zero_grad()
        pred_train = model(X_train)
        loss = criterion(pred_train, y_train)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_loss = criterion(model(X_val), y_val).item()
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)

    # ── Compute val MAPE ──────────────────────────────────────────────────────
    model.eval()
    with torch.no_grad():
        val_pred_scaled = model(X_val).squeeze().numpy()
    val_pred = scaler_y.inverse_transform(val_pred_scaled.reshape(-1, 1)).ravel()
    val_true = scaler_y.inverse_transform(y_val.squeeze().numpy().reshape(-1, 1)).ravel()
    mape = float(np.mean(np.abs((val_true - val_pred) / (np.abs(val_true) + 1e-9))) * 100)

    # ── Persist ───────────────────────────────────────────────────────────────
    version = next_version_tag("lstm", ticker)
    d = _ticker_dir("lstm", ticker)
    torch.save(best_state, d / f"{version}.pt")
    joblib.dump(
        {"scaler_X": scaler_X, "scaler_y": scaler_y, "features": available},
        d / f"{version}_scaler.pkl",
    )

    meta = {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "features_used": available,
        "mape": round(mape, 4),
        "n_samples": len(X_list),
        "seq_len": SEQ_LEN,
        "n_features": len(available),
        "forward_days": FORWARD_DAYS,
    }
    save_metadata("lstm", ticker, meta)

    logger.info(
        f"LSTM trained: ticker={ticker} version={version} mape={mape:.2f}%",
        extra={"ticker": ticker, "model_version": version, "mape": mape},
    )
    return meta

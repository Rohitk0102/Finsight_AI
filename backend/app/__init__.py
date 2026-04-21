import warnings
import os

# ── Global Warning Suppression ───────────────────────────────────────────────
# This must run before any other imports to catch yfinance/pandas noise.
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Silence the specific Pandas4Warning from yfinance
warnings.filterwarnings("ignore", message=".*Pandas4Warning.*")
warnings.filterwarnings("ignore", message=".*Timestamp.utcnow.*")

# Also set environment variable for child processes
os.environ["PYTHONWARNINGS"] = "ignore"

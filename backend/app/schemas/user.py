from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class InvestmentHorizon(str, Enum):
    SHORT = "short"    # < 1 month
    MEDIUM = "medium"  # 1–6 months
    LONG = "long"      # > 6 months


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    risk_profile: Optional[RiskProfile] = None
    investment_horizon: Optional[InvestmentHorizon] = None
    preferred_sectors: Optional[list[str]] = None
    investment_amount: Optional[float] = None


class UserProfile(BaseModel):
    model_config = {"populate_by_name": True}

    id: str = Field(alias="clerk_id")
    email: str
    full_name: Optional[str] = None
    risk_profile: RiskProfile = RiskProfile.MODERATE
    investment_horizon: InvestmentHorizon = InvestmentHorizon.MEDIUM
    preferred_sectors: list[str] = []
    investment_amount: Optional[float] = None
    created_at: Optional[datetime] = None



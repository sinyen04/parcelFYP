"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


# ── Auth ─────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Video ────────────────────────────────────────────────────────────

class VideoOut(BaseModel):
    id: int
    filename: str
    status: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoStatusOut(BaseModel):
    id: int
    status: str
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Parcel ───────────────────────────────────────────────────────────

class ParcelOut(BaseModel):
    id: int
    video_id: int
    track_id: int
    condition: str
    confidence_score: float
    image_path: Optional[str] = None
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    action: str
    detected_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ParcelListOut(BaseModel):
    parcels: list[ParcelOut]
    total: int


# ── Dashboard ────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_detected: int
    total_damaged: int
    total_undamaged: int

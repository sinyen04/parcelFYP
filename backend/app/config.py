"""
Configuration module for Parcel Condition Detection System.

KEY SWITCH: USE_MOCK_MODEL
  - True  → uses mock_inference.py (fake detections for testing)
  - False → uses inference.py (real YOLO model at MODEL_WEIGHTS_PATH)

To switch to the real model:
  1. Place your trained best.pt at backend/ml/weights/best.pt
  2. Set USE_MOCK_MODEL=False in backend/.env
  3. Restart the backend server
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from the backend directory
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")


class Settings(BaseSettings):
    # ── Model toggle ─────────────────────────────────────────────────
    # >>> SWITCH: set to False once you have a real best.pt <<<
    USE_MOCK_MODEL: bool = True
    MODEL_WEIGHTS_PATH: str = str(_backend_dir / "ml" / "weights" / "best.pt")

    # ── Tracking ─────────────────────────────────────────────────────
    # Parcel confirmation threshold in seconds
    CONFIRMATION_THRESHOLD_SECONDS: float = 5.0

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str = f"sqlite:///{_backend_dir / 'parcel_detection.db'}"

    # ── Auth / JWT ───────────────────────────────────────────────────
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── File storage ─────────────────────────────────────────────────
    UPLOAD_DIR: str = str(_backend_dir / "uploads")
    VIDEO_DIR: str = str(_backend_dir / "uploads" / "videos")
    CROP_DIR: str = str(_backend_dir / "uploads" / "crops")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Ensure upload directories exist
os.makedirs(settings.VIDEO_DIR, exist_ok=True)
os.makedirs(settings.CROP_DIR, exist_ok=True)

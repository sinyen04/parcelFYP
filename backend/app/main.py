"""
Parcel Condition Detection System — FastAPI Application Entry Point.

Starts the server, sets up CORS, includes all routers,
creates database tables, seeds the test user, and serves crop images.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, SessionLocal
from app.models import Base
from app.routers import auth, videos, parcels, dashboard
from app.routers.auth import seed_test_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    # ── Startup ──────────────────────────────────────────────────────
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

    # Seed test user (admin / admin123)
    db = SessionLocal()
    try:
        seed_test_user(db)
        logger.info("Test user seeded (admin / admin123)")
    finally:
        db.close()

    logger.info(f"USE_MOCK_MODEL = {settings.USE_MOCK_MODEL}")
    logger.info("Parcel Condition Detection System is ready!")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    logger.info("Shutting down...")


# Create the FastAPI app
app = FastAPI(
    title="Parcel Condition Detection System",
    description="Upload parcel videos, detect damaged/undamaged parcels using YOLO, and browse results.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────
# Permissive CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (serve crop images) ────────────────────────────────
app.mount("/crops", StaticFiles(directory=settings.CROP_DIR), name="crops")

# ── Include routers ─────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(parcels.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "mock_mode": settings.USE_MOCK_MODEL}

"""
Dashboard summary endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Parcel
from app.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    """
    Return aggregate counts of all detected parcels across all videos.
    """
    total_detected = db.query(Parcel).count()
    total_damaged = db.query(Parcel).filter(Parcel.condition == "damaged").count()
    total_undamaged = db.query(Parcel).filter(Parcel.condition == "undamaged").count()

    return DashboardSummary(
        total_detected=total_detected,
        total_damaged=total_damaged,
        total_undamaged=total_undamaged,
    )

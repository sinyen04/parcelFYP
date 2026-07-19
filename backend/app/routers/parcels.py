"""
Parcel listing and detail endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Parcel
from app.schemas import ParcelOut, ParcelListOut

router = APIRouter(prefix="/parcels", tags=["parcels"])


@router.get("", response_model=ParcelListOut)
def list_parcels(
    condition: Optional[str] = Query(None, description="Filter by 'damaged' or 'undamaged'"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Return paginated parcel records, optionally filtered by condition.
    """
    query = db.query(Parcel)
    if condition:
        query = query.filter(Parcel.condition == condition)

    total = query.count()
    parcels = query.order_by(Parcel.detected_at.desc()).offset(offset).limit(limit).all()

    return ParcelListOut(parcels=parcels, total=total)


@router.get("/{parcel_id}", response_model=ParcelOut)
def get_parcel(parcel_id: int, db: Session = Depends(get_db)):
    """Return the full detail record for a single parcel."""
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel

"""
SQLAlchemy ORM models for the Parcel Condition Detection System.

Tables:
  - videos:  uploaded video metadata + processing status
  - parcels: detected parcel records linked to a video
  - users:   authentication accounts
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | processing | completed | failed
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)

    # Relationship
    parcels = relationship("Parcel", back_populates="video", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Video id={self.id} filename={self.filename} status={self.status}>"


class Parcel(Base):
    __tablename__ = "parcels"
    __table_args__ = (
        UniqueConstraint("video_id", "track_id", name="uq_video_track"),
    )

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    track_id = Column(Integer, nullable=False)
    condition = Column(String, nullable=False)       # "damaged" | "undamaged"
    confidence_score = Column(Float, nullable=False)
    image_path = Column(String, nullable=True)       # path to cropped image
    bbox_x = Column(Integer, nullable=False)
    bbox_y = Column(Integer, nullable=False)
    bbox_w = Column(Integer, nullable=False)
    bbox_h = Column(Integer, nullable=False)
    action = Column(String, nullable=False)           # "inspection" | "normal_line"
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    video = relationship("Video", back_populates="parcels")

    def __repr__(self):
        return f"<Parcel id={self.id} track_id={self.track_id} condition={self.condition}>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"

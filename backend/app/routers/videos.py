"""
Video upload and status endpoints.
"""

import os
import uuid
import queue
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Video
from app.schemas import VideoOut, VideoStatusOut
from app.config import settings
from app.worker import process_video_task
from app.ml.pipeline import active_streams

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/upload", response_model=VideoOut)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Accept a multipart video file upload.
    Saves the file, creates a DB record, and schedules background processing.
    """
    # Generate a unique filename to avoid collisions
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(settings.VIDEO_DIR, unique_name)

    # Save the file to disk
    contents = await file.read()
    with open(save_path, "wb") as f:
        f.write(contents)

    # Create database record
    video = Video(
        filename=file.filename,
        storage_path=save_path,
        status="pending",
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Schedule background processing
    background_tasks.add_task(process_video_task, video.id)

    return video


@router.get("/{video_id}/status", response_model=VideoStatusOut)
def get_video_status(video_id: int, db: Session = Depends(get_db)):
    """Return the current processing status of a video."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.get("/{video_id}/stream")
def stream_video(video_id: int, db: Session = Depends(get_db)):
    """
    Stream the live processing of a video using MJPEG.
    Connects to the active_streams queue from pipeline.py.
    """
    # Verify video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # If already completed or failed, we can't stream live processing
    if video.status in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Video processing already finished")

    # Initialize queue for this client
    q = queue.Queue(maxsize=30)
    if video_id not in active_streams:
        active_streams[video_id] = []
    active_streams[video_id].append(q)

    def generate_frames():
        try:
            while True:
                # Need fresh DB session/query to check status because we are yielding
                current_video = db.query(Video).filter(Video.id == video_id).first()
                if current_video:
                    db.refresh(current_video) # Force SQLAlchemy to fetch latest data, ignoring cache
                
                if current_video and current_video.status in ["completed", "failed"] and q.empty():
                    break
                
                try:
                    frame_bytes = q.get(timeout=1.0)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except queue.Empty:
                    continue
        finally:
            # Cleanup queue on disconnect or finish
            if video_id in active_streams and q in active_streams[video_id]:
                active_streams[video_id].remove(q)
                if not active_streams[video_id]:
                    del active_streams[video_id]

    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


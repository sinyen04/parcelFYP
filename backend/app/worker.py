"""
Background worker for processing uploaded videos.

Uses FastAPI BackgroundTasks — no need for Celery/Redis at this stage.
This module is called by the video upload endpoint to process videos
asynchronously after they are uploaded.
"""

import logging
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import Video
from app.ml.pipeline import process_video

logger = logging.getLogger(__name__)


def process_video_task(video_id: int):
    """
    Background task that processes a single video.

    Workflow:
      1. Set video status to 'processing'
      2. Run the ML pipeline
      3. Set video status to 'completed' (or 'failed' on error)
    """
    # Create a new DB session for the background task
    db = SessionLocal()

    try:
        # 1. Mark as processing
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"Video {video_id} not found in database")
            return

        video.status = "processing"
        db.commit()
        logger.info(f"Video {video_id} status → processing")

        # 2. Run the pipeline
        process_video(
            video_path=video.storage_path,
            video_id=video.id,
            db=db,
        )

        # 3. Mark as completed
        video.status = "completed"
        video.processed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Video {video_id} status → completed")

    except Exception as e:
        logger.exception(f"Video {video_id} processing failed: {e}")
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = "failed"
                db.commit()
        except Exception:
            logger.exception("Failed to update video status to 'failed'")
    finally:
        db.close()

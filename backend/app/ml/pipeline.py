"""
Processing pipeline that orchestrates video frame extraction and inference.

KEY SWITCH: This module picks real YOLO or mock inference based on
            config.USE_MOCK_MODEL. Both produce identical output shapes,
            so the rest of the code is agnostic.

Workflow:
  1. Read video frame-by-frame with OpenCV
  2. Run inference (real or mock) on each frame
  3. For each unique track_id, keep only the highest-confidence detection
  4. Crop the best detection region and save as an image
  5. Insert/upsert parcel records into the database
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional

import cv2
import numpy as np
from sqlalchemy.orm import Session
import queue

from app.config import settings
from app.models import Parcel

logger = logging.getLogger(__name__)

# Global dictionary to hold active stream queues for MJPEG broadcast
# { video_id: [queue.Queue, queue.Queue, ...] }
active_streams: dict[int, list[queue.Queue]] = {}



def process_video(video_path: str, video_id: int, db: Session):
    """
    Full processing pipeline for a single video.

    Args:
        video_path: absolute path to the video file on disk
        video_id: database ID of the Video record
        db: SQLAlchemy session
    """
    logger.info(f"Starting pipeline for video {video_id}: {video_path}")

    # ── SWITCH: pick inference backend ──────────────────────────────
    if settings.USE_MOCK_MODEL:
        # >>> MOCK MODE: no real model needed <<<
        from app.ml.mock_inference import run_mock_inference_on_frame, reset_mock_state
        reset_mock_state()
        logger.info("Using MOCK inference (USE_MOCK_MODEL=True)")
    else:
        # >>> REAL MODE: requires best.pt at MODEL_WEIGHTS_PATH <<<
        from app.ml.inference import run_inference_on_frame
        logger.info(f"Using REAL YOLO inference (model: {settings.MODEL_WEIGHTS_PATH})")
    # ────────────────────────────────────────────────────────────────

    # Open the video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"Video: {total_frames} frames at {fps} FPS")

    # Accumulate best detection per track_id
    # { track_id: { "detection": dict, "frame": np.ndarray } }
    best_detections: dict[int, dict] = {}

    # Calculate confirmation threshold in frames
    confirmation_frames = int(settings.CONFIRMATION_THRESHOLD_SECONDS * fps)
    
    # Track confirmation states
    track_frame_counts: dict[int, int] = {}
    confirmed_tracks: set[int] = set()

    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = frame_index / fps

        # ── Run inference (mock or real) ────────────────────────────
        if settings.USE_MOCK_MODEL:
            detections = run_mock_inference_on_frame(
                frame=frame,
                frame_timestamp=timestamp,
                frame_index=frame_index,
                total_frames=total_frames,
            )
        else:
            detections = run_inference_on_frame(
                frame=frame,
                weights_path=settings.MODEL_WEIGHTS_PATH,
                frame_timestamp=timestamp,
            )
        # ────────────────────────────────────────────────────────────

        # ── Update Track Frame Counts and Confirmations ─────────────
        for det in detections:
            tid = det["track_id"]
            track_frame_counts[tid] = track_frame_counts.get(tid, 0) + 1
            if track_frame_counts[tid] >= confirmation_frames:
                confirmed_tracks.add(tid)
        # ────────────────────────────────────────────────────────────

        # ── Live Streaming: Draw annotations and push to queue ──────
        if video_id in active_streams and active_streams[video_id]:
            # Draw on a copy of the frame for the stream
            stream_frame = frame.copy()
            for det in detections:
                tid = det["track_id"]
                x, y, w, h = det["bbox"]
                
                count = track_frame_counts.get(tid, 0)
                if tid in confirmed_tracks:
                    label = f'CAPTURED | {det["condition"]} {det["confidence"]:.2f}'
                    color = (0, 255, 255)  # Yellow for captured
                else:
                    label = f'{count}/{confirmation_frames} frames | {det["condition"]}'
                    color = (0, 165, 255)  # Orange for in-progress

                cv2.rectangle(stream_frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(stream_frame, label, (x, max(10, y - 10)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', stream_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                # Push to all active listener queues for this video
                for q in active_streams[video_id]:
                    try:
                        q.put_nowait(frame_bytes)
                    except queue.Full:
                        # Drop frame if queue is full to avoid blocking the worker
                        pass
        # ────────────────────────────────────────────────────────────

        # Keep only the highest-confidence detection per track_id
        for det in detections:
            tid = det["track_id"]
            if tid not in best_detections or det["confidence"] > best_detections[tid]["detection"]["confidence"]:
                best_detections[tid] = {
                    "detection": det,
                    "frame": frame.copy(),
                }

        frame_index += 1

    cap.release()
    logger.info(f"Extracted {len(best_detections)} unique tracks from {frame_index} frames")

    # ── Save crops and write to database ────────────────────────────
    for track_id, data in best_detections.items():
        if track_id not in confirmed_tracks:
            continue  # Skip short-lived/spurious tracks
            
        det = data["detection"]
        frame = data["frame"]
        x, y, w, h = det["bbox"]

        # Crop the region from the frame
        frame_h, frame_w = frame.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(frame_w, x + w)
        y2 = min(frame_h, y + h)
        crop = frame[y1:y2, x1:x2]

        # Save the crop image
        crop_filename = f"video_{video_id}_track_{track_id}.jpg"
        crop_path = os.path.join(settings.CROP_DIR, crop_filename)

        if crop.size > 0:
            cv2.imwrite(crop_path, crop)
        else:
            # Create a placeholder image if crop is empty
            placeholder = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.putText(placeholder, "N/A", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imwrite(crop_path, placeholder)

        # Derive action from condition
        action = "inspection" if det["condition"] == "damaged" else "normal_line"

        # Upsert parcel record (unique on video_id + track_id)
        existing = db.query(Parcel).filter(
            Parcel.video_id == video_id,
            Parcel.track_id == track_id,
        ).first()

        if existing:
            existing.condition = det["condition"]
            existing.confidence_score = det["confidence"]
            existing.image_path = crop_filename
            existing.bbox_x = x
            existing.bbox_y = y
            existing.bbox_w = w
            existing.bbox_h = h
            existing.action = action
            existing.detected_at = datetime.now(timezone.utc)
        else:
            parcel = Parcel(
                video_id=video_id,
                track_id=track_id,
                condition=det["condition"],
                confidence_score=det["confidence"],
                image_path=crop_filename,
                bbox_x=x,
                bbox_y=y,
                bbox_w=w,
                bbox_h=h,
                action=action,
                detected_at=datetime.now(timezone.utc),
            )
            db.add(parcel)

    db.commit()
    logger.info(f"Pipeline complete for video {video_id}: {len(best_detections)} parcels written to DB")

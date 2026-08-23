"""
WebSocket endpoint for real-time webcam parcel detection.

Receives JPEG frames from the browser webcam, runs inference,
and sends back annotated frames + detection data.
"""

import base64
import logging
import os
from datetime import datetime, timezone

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Video, Parcel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webcam"])


@router.websocket("/ws/webcam")
async def webcam_detect(ws: WebSocket):
    """
    WebSocket endpoint for live webcam detection.

    Protocol:
      Client → Server:  binary JPEG frame
      Server → Client:  JSON { annotated_frame, detections, stats }
    """
    await ws.accept()
    logger.info("Webcam WebSocket connected")

    # ── Create DB session and Video record for this session ──────────
    db: Session = SessionLocal()
    video = Video(
        filename="webcam_session",
        storage_path="webcam",
        status="processing",
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    video_id = video.id
    logger.info(f"Created webcam session Video id={video_id}")

    # ── Load inference backend (same switch as pipeline.py) ──────────
    if settings.USE_MOCK_MODEL:
        from app.ml.mock_inference import run_mock_inference_on_frame, reset_mock_state
        reset_mock_state()
        logger.info("Webcam: using MOCK inference")
    else:
        from app.ml.inference import run_inference_on_frame
        logger.info("Webcam: using REAL YOLO inference")

    # ── Tracking state ───────────────────────────────────────────────
    best_detections: dict[int, dict] = {}
    track_frame_counts: dict[int, int] = {}
    confirmed_tracks: set[int] = set()

    fps_estimate = 5.0  # approximate FPS from webcam capture rate
    confirmation_frames = int(settings.CONFIRMATION_THRESHOLD_SECONDS * fps_estimate)
    frame_index = 0

    try:
        while True:
            # Receive binary JPEG frame from client
            data = await ws.receive_bytes()

            # Decode JPEG → OpenCV BGR frame
            np_arr = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            timestamp = frame_index / fps_estimate

            # ── Run inference ────────────────────────────────────────
            if settings.USE_MOCK_MODEL:
                detections = run_mock_inference_on_frame(
                    frame=frame,
                    frame_timestamp=timestamp,
                    frame_index=frame_index,
                    total_frames=9999,  # unknown for webcam
                )
            else:
                detections = run_inference_on_frame(
                    frame=frame,
                    weights_path=settings.MODEL_WEIGHTS_PATH,
                    frame_timestamp=timestamp,
                    conf_threshold=settings.CONFIDENCE_THRESHOLD,
                )

            # ── Update track confirmation counts ─────────────────────
            for det in detections:
                tid = det["track_id"]
                track_frame_counts[tid] = track_frame_counts.get(tid, 0) + 1
                if track_frame_counts[tid] >= confirmation_frames:
                    confirmed_tracks.add(tid)

            # ── Keep best detection per track ────────────────────────
            for det in detections:
                tid = det["track_id"]
                if tid not in best_detections or det["confidence"] > best_detections[tid]["detection"]["confidence"]:
                    best_detections[tid] = {
                        "detection": det,
                        "frame": frame.copy(),
                    }

            # ── Draw annotations on frame ────────────────────────────
            annotated = frame.copy()
            det_list = []
            for det in detections:
                tid = det["track_id"]
                x, y, w, h = det["bbox"]
                count = track_frame_counts.get(tid, 0)

                if tid in confirmed_tracks:
                    label = f'CAPTURED | {det["condition"]} {det["confidence"]:.2f}'
                    color = (0, 255, 255)  # Yellow
                else:
                    label = f'{count}/{confirmation_frames} frames | {det["condition"]}'
                    color = (0, 165, 255)  # Orange

                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
                cv2.putText(annotated, label, (x, max(10, y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                det_list.append({
                    "track_id": tid,
                    "condition": det["condition"],
                    "confidence": round(det["confidence"], 4),
                    "bbox": [x, y, w, h],
                    "confirmed": tid in confirmed_tracks,
                })

            # ── Encode annotated frame → base64 JPEG ─────────────────
            _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64_frame = base64.b64encode(buf.tobytes()).decode("ascii")

            # ── Compute stats ────────────────────────────────────────
            total_confirmed = len(confirmed_tracks)
            damaged = sum(
                1 for tid in confirmed_tracks
                if tid in best_detections and best_detections[tid]["detection"]["condition"] == "damaged"
            )
            undamaged = total_confirmed - damaged

            # ── Send response ────────────────────────────────────────
            await ws.send_json({
                "annotated_frame": b64_frame,
                "detections": det_list,
                "stats": {
                    "total_confirmed": total_confirmed,
                    "damaged": damaged,
                    "undamaged": undamaged,
                },
                "frame_index": frame_index,
            })

            frame_index += 1

    except WebSocketDisconnect:
        logger.info(f"Webcam WebSocket disconnected (video_id={video_id})")
    except Exception as e:
        logger.exception(f"Webcam WebSocket error: {e}")
    finally:
        # ── Save confirmed parcels to DB ─────────────────────────────
        saved_count = 0
        for track_id, data in best_detections.items():
            if track_id not in confirmed_tracks:
                continue

            det = data["detection"]
            frame_img = data["frame"]
            x, y, w, h = det["bbox"]

            # Crop and save image
            frame_h, frame_w = frame_img.shape[:2]
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(frame_w, x + w), min(frame_h, y + h)
            crop = frame_img[y1:y2, x1:x2]

            crop_filename = f"webcam_{video_id}_track_{track_id}.jpg"
            crop_path = os.path.join(settings.CROP_DIR, crop_filename)

            if crop.size > 0:
                cv2.imwrite(crop_path, crop)
            else:
                placeholder = np.zeros((100, 100, 3), dtype=np.uint8)
                cv2.putText(placeholder, "N/A", (20, 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.imwrite(crop_path, placeholder)

            action = "inspection" if det["condition"] == "damaged" else "normal_line"

            # Upsert parcel record
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
            saved_count += 1

        # Mark video as completed
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = "completed"
            video.processed_at = datetime.now(timezone.utc)
        db.commit()
        db.close()
        logger.info(f"Webcam session {video_id} complete: {saved_count} parcels saved")

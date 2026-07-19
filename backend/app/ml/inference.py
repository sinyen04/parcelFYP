"""
Real YOLO inference pipeline using ultralytics.

This module loads a trained YOLOv8 model and runs detection + ByteTrack
tracking on video frames. The output format matches mock_inference.py
exactly so pipeline.py can use them interchangeably.

SWITCH: This module is used when config.USE_MOCK_MODEL = False.
        It requires a valid model weights file at config.MODEL_WEIGHTS_PATH.
"""

import logging
from pathlib import Path
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

# The model is loaded lazily on first use
_model = None


def load_model(weights_path: str):
    """
    Load the YOLO model from the given weights path.
    Called once when the first video is processed.
    """
    global _model
    from ultralytics import YOLO  # imported here to avoid import errors if ultralytics not installed

    path = Path(weights_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model weights not found at {weights_path}. "
            f"Either place your best.pt there or set USE_MOCK_MODEL=True in .env"
        )

    logger.info(f"Loading YOLO model from {weights_path}")
    _model = YOLO(str(path))
    logger.info("YOLO model loaded successfully")
    return _model


def run_inference_on_frame(
    frame: np.ndarray,
    weights_path: str,
    frame_timestamp: float,
    conf_threshold: float = 0.25,
) -> list[dict]:
    """
    Run YOLO detection + ByteTrack tracking on a single frame.

    Args:
        frame: BGR numpy array (OpenCV format)
        weights_path: path to model weights
        frame_timestamp: timestamp of this frame in seconds
        conf_threshold: minimum confidence threshold

    Returns:
        List of detection dicts with the standard schema:
        [
            {
                "track_id": int,
                "condition": "damaged" | "undamaged",
                "confidence": float,
                "bbox": (x, y, w, h),
                "frame_timestamp": float,
            },
            ...
        ]
    """
    global _model

    # Lazy-load the model
    if _model is None:
        load_model(weights_path)

    # Run tracking with ByteTrack (persist=True keeps track IDs across frames)
    results = _model.track(
        frame,
        persist=True,
        conf=conf_threshold,
        tracker="bytetrack.yaml",
        verbose=False,
    )

    detections = []
    for result in results:
        if result.boxes is None or len(result.boxes) == 0:
            continue

        boxes = result.boxes
        for i in range(len(boxes)):
            # Get bounding box in xyxy format and convert to xywh
            x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy().astype(int)
            w = x2 - x1
            h = y2 - y1

            # Get track ID (may be None if tracking failed for this box)
            track_id = None
            if boxes.id is not None:
                track_id = int(boxes.id[i].cpu().numpy())

            if track_id is None:
                continue  # skip untracked detections

            # Get confidence
            conf = float(boxes.conf[i].cpu().numpy())

            # Get class — map class index to condition
            # Assumes: class 0 = "damaged", class 1 = "undamaged"
            # Adjust these mappings based on your actual model's class names
            cls_id = int(boxes.cls[i].cpu().numpy())
            class_names = _model.names  # e.g. {0: "damaged", 1: "undamaged"}
            condition = class_names.get(cls_id, "undamaged")

            detections.append({
                "track_id": track_id,
                "condition": condition,
                "confidence": conf,
                "bbox": (int(x1), int(y1), int(w), int(h)),
                "frame_timestamp": frame_timestamp,
            })

    return detections

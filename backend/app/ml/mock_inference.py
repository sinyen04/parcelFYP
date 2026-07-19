"""
Mock inference generator for testing without a trained YOLO model.

Produces plausible fake detections with random bounding boxes, random
conditions ("damaged" / "undamaged"), and random confidence scores
between 0.5–0.99. The output shape is identical to inference.py so
pipeline.py never needs to know which produced the data.

SWITCH: This module is used when config.USE_MOCK_MODEL = True (default).
"""

import random
import logging

logger = logging.getLogger(__name__)

# Persistent state for mock tracking IDs (simulates ByteTrack persistence)
_mock_tracks: dict[int, dict] = {}
_next_track_id: int = 1
_initialized: bool = False


def _initialize_mock_tracks(num_parcels: int = None):
    """Initialize a set of mock tracked parcels for the video."""
    global _mock_tracks, _next_track_id, _initialized

    if num_parcels is None:
        num_parcels = random.randint(5, 15)  # random number of parcels per video

    _mock_tracks = {}
    for i in range(num_parcels):
        tid = _next_track_id + i
        condition = random.choice(["damaged", "undamaged"])
        _mock_tracks[tid] = {
            "condition": condition,
            "base_confidence": random.uniform(0.5, 0.99),
            "base_x": random.randint(50, 500),
            "base_y": random.randint(50, 400),
            "base_w": random.randint(60, 200),
            "base_h": random.randint(60, 200),
        }

    _next_track_id += num_parcels
    _initialized = True
    logger.info(f"Mock inference initialized with {num_parcels} fake parcels")


def reset_mock_state():
    """Reset mock state for a new video processing run."""
    global _mock_tracks, _initialized
    _mock_tracks = {}
    _initialized = False


def run_mock_inference_on_frame(
    frame,  # numpy array, not actually used — just for API compatibility
    frame_timestamp: float,
    frame_index: int,
    total_frames: int,
) -> list[dict]:
    """
    Generate plausible fake detections for a single frame.

    Returns the exact same data shape as inference.run_inference_on_frame():
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
    global _initialized

    if not _initialized:
        _initialize_mock_tracks()

    detections = []

    # Not every track appears in every frame (simulates parcels entering/leaving view)
    for track_id, track_info in _mock_tracks.items():
        # Each parcel has a ~70% chance of being visible in any given frame
        if random.random() > 0.7:
            continue

        # Add some jitter to simulate movement between frames
        jitter_x = random.randint(-10, 10)
        jitter_y = random.randint(-10, 10)

        # Vary confidence slightly per frame
        conf = min(0.99, max(0.5, track_info["base_confidence"] + random.uniform(-0.05, 0.05)))

        detections.append({
            "track_id": track_id,
            "condition": track_info["condition"],
            "confidence": round(conf, 4),
            "bbox": (
                max(0, track_info["base_x"] + jitter_x),
                max(0, track_info["base_y"] + jitter_y),
                track_info["base_w"],
                track_info["base_h"],
            ),
            "frame_timestamp": frame_timestamp,
        })

    return detections

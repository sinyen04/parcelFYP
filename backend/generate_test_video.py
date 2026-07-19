"""Generate a short synthetic test video for testing the upload pipeline."""
import cv2
import numpy as np
import os

# Create a simple 3-second video with colored rectangles simulating parcels
output_path = os.path.join(os.path.dirname(__file__), "uploads", "test_video.mp4")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

width, height = 640, 480
fps = 30
duration = 3  # seconds
total_frames = fps * duration

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

for i in range(total_frames):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = (30, 30, 40)  # dark background
    
    # Draw some moving rectangles to simulate parcels
    offset = int(20 * np.sin(i * 0.1))
    
    # Parcel 1 (brownish box)
    cv2.rectangle(frame, (100 + offset, 100), (250 + offset, 200), (60, 120, 180), -1)
    cv2.rectangle(frame, (100 + offset, 100), (250 + offset, 200), (80, 150, 220), 2)
    cv2.putText(frame, "Parcel 1", (110 + offset, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Parcel 2 (damaged look - reddish)
    cv2.rectangle(frame, (350 - offset, 150), (500 - offset, 280), (50, 50, 180), -1)
    cv2.rectangle(frame, (350 - offset, 150), (500 - offset, 280), (80, 80, 220), 2)
    cv2.putText(frame, "Parcel 2", (360 - offset, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Parcel 3
    cv2.rectangle(frame, (200, 300 + offset), (380, 420 + offset), (100, 160, 60), -1)
    cv2.rectangle(frame, (200, 300 + offset), (380, 420 + offset), (130, 200, 80), 2)
    cv2.putText(frame, "Parcel 3", (220, 370 + offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    out.write(frame)

out.release()
print(f"Test video created: {output_path}")
print(f"Duration: {duration}s, FPS: {fps}, Resolution: {width}x{height}")

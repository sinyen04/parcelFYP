import os
import cv2
import time
from ultralytics import YOLO

# ==========================================
# CONFIGURATION PATHS
# ==========================================
# Update these paths to match your actual Detection dataset and weights
WEIGHTS_PATH = r"G:\My Drive\Parcel\output\parcel-1\yolo8_run_01\weights\best.pt"
DATA_YAML = r"G:\My Drive\Parcel\datasets\parcel-1\data.yaml"
TEST_VISUALS_DIR = r"G:\My Drive\Parcel\datasets\parcel-1\test\images"

# Your requested output directory
OUTPUT_DIR = r"G:\My Drive\Parcel\test_outputs"

# ==========================================
# MAIN EVALUATION FUNCTION
# ==========================================
def evaluate_detection_model():
    print(f"Loading YOLO Detection model from: {WEIGHTS_PATH}")
    model = YOLO(WEIGHTS_PATH)
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ---------------------------------------------------------
    # 1. BUILT-IN YOLO VALIDATION (mAP, Precision, Recall)
    # ---------------------------------------------------------
    print("\n" + "=" * 50)
    print(" 📊 RUNNING YOLO BUILT-IN VALIDATION")
    print("=" * 50)
    
    # Run validation and force it to save results to your output folder
    metrics = model.val(
        data=DATA_YAML, 
        split='test',
        project=OUTPUT_DIR,
        name='validation_metrics',
        exist_ok=True
    )

    # Add this to automatically save your metrics to a text file
    metrics_log_path = os.path.join(OUTPUT_DIR, "validation_metrics", "metrics_summary.txt")
    with open(metrics_log_path, "w") as f:
        f.write("=== DETECTION METRICS SUMMARY ===\n")
        f.write(f"mAP@50:    {metrics.box.map50:.4f}\n")
        f.write(f"mAP@50-95: {metrics.box.map:.4f}\n")
        f.write(f"Precision: {metrics.box.mp:.4f}\n")
        f.write(f"Recall:    {metrics.box.mr:.4f}\n")

    print("\n" + "=" * 50)
    print(" 🎯 DETECTION METRICS SUMMARY")
    print("=" * 50)
    print(f" mAP@50:    {metrics.box.map50:.4f}  (Main overall accuracy score)")
    print(f" mAP@50-95: {metrics.box.map:.4f}  (Strict bounding box accuracy)")
    print(f" Precision: {metrics.box.mp:.4f}  (Accuracy of bounding box detections)")
    print(f" Recall:    {metrics.box.mr:.4f}  (Detection coverage rate)")
    print("=" * 50)

    # ---------------------------------------------------------
    # 2. PRACTICAL PIPELINE & SAVING VISUAL OUTPUTS
    # ---------------------------------------------------------
    print(f"\nProcessing test visuals and saving to: {OUTPUT_DIR}\n")
    
    total_images = 0
    total_processing_time = 0.0

    # Create a subfolder specifically for the drawn images
    predictions_dir = os.path.join(OUTPUT_DIR, "predicted_visuals")
    os.makedirs(predictions_dir, exist_ok=True)

    for filename in os.listdir(TEST_VISUALS_DIR):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
            
        image_path = os.path.join(TEST_VISUALS_DIR, filename)
        raw_image = cv2.imread(image_path)
        
        if raw_image is None:
            print(f"Failed to read {filename}. Skipping.")
            continue

        total_images += 1
        
        # START TIMING ⏱️
        start_time = time.time()
        
        # Run inference (conf=0.25 is a standard starting point for detection)
        results = model(raw_image, conf=0.25, verbose=False)
        
        # STOP TIMING ⏱️
        process_time = time.time() - start_time
        total_processing_time += process_time
        
        # Plot the bounding boxes on the image
        annotated_image = results[0].plot()
        
        # Save the annotated image to your designated folder
        save_path = os.path.join(predictions_dir, filename)
        cv2.imwrite(save_path, annotated_image)

    # Calculate Speed Metrics
    avg_time_ms = (total_processing_time / total_images) * 1000 if total_images > 0 else 0.0
    
    print("\n" + "=" * 50)
    print(" ⏱️ INFERENCE SPEED SUMMARY")
    print("=" * 50)
    print(f" Total Visuals Processed: {total_images}")
    print(f" Avg Time per Image:      {avg_time_ms:.1f} ms")
    print(f" All outputs successfully saved to: {OUTPUT_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    evaluate_detection_model()
"""
BeeGuardAI - YOLO Object Detection Training
Fine-tune YOLOv8 to detect and count bees and hornets.
"""

import argparse
from pathlib import Path
from ultralytics import YOLO

def train(model_name="yolov8n", epochs=100, imgsz=640, batch=16):
    """Train YOLOv8 on bee/hornet dataset"""

    print("=" * 60)
    print("BeeGuardAI - YOLO Training")
    print("=" * 60)

    # --- PATH MANAGEMENT ---
    # BASE_DIR is the 'ml-training' folder
    BASE_DIR = Path(__file__).resolve().parent
    
    # Use the local config.yaml file
    data_config = (BASE_DIR / "config.yaml").resolve()
    
    # Image folders for verification
    train_path = (BASE_DIR / "data" / "train" / "images").resolve()
    val_path = (BASE_DIR / "data" / "val" / "images").resolve()

    # --- DATASET CHECK ---
    if not train_path.exists():
        print(f"\n⚠️  Dataset NOT found at: {train_path}")
        print("Please ensure your 'data' folder is inside 'ml-training'.")
        return

    # --- LOAD MODEL ---
    print(f"\nLoading pretrained {model_name}.pt...")
    model = YOLO(f"{model_name}.pt")

    # --- START TRAINING ---
    # We pass the absolute path string of the config to YOLO
    print(f"\nTraining for {epochs} epochs...")
    model.train(
        data=str(data_config),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name="bee_hornet_detector",
        project="models",
        exist_ok=True,
        patience=20,
        save=True,
        plots=True,
    )

    best_model_path = Path("models/bee_hornet_detector/weights/best.pt")
    print(f"\n✓ Best model saved to: {best_model_path}")

    # Final validation
    print("\nValidating results...")
    metrics = model.val()
    print(f"mAP50: {metrics.box.map50:.3f}")

    return model

def main():
    parser = argparse.ArgumentParser(description="Train YOLO for bee/hornet detection")
    parser.add_argument("--model", type=str, default="yolov8n", choices=["yolov8n", "yolov8s", "yolov8m"])
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)

    args = parser.parse_args()
    train(model_name=args.model, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch)

if __name__ == "__main__":
    main()
"""
BeeGuardAI - YOLO Inference Script
Runs detection on images and outputs SensorData-compatible format.

Output format:
{
    "ruche_id": int,
    "nombre_frelons": int,           # hornet count
    "nombre_abeilles_entrees": int,  # bee count
    "nombre_abeilles_sorties": 0,    # not detected by vision
    "temperature": 0.0,              # from other sensors
    "humidite": 0.0,                 # from other sensors
    "etat_abeilles": "normal",       # inferred from counts
    "etat_acoustique": "normal"      # from audio sensor
}

Usage:
    python inference.py --image path/to/image.jpg
    python inference.py --folder path/to/images/
    python inference.py --image img.jpg --visualize  # Show bounding boxes
"""

import argparse
import json
import cv2
from pathlib import Path
from ultralytics import YOLO


class BeeHornetDetector:
    def __init__(self, model_path="models/bee_hornet_detector/weights/best.pt"):
        self.model_path = model_path
        self.classes = {0: "bee", 1: "hornet"}
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the YOLO model"""
        path = Path(self.model_path)
        if not path.exists():
            print(f"Model not found: {self.model_path}")
            print("Run train.py first or download a pretrained model.")
            return

        self.model = YOLO(self.model_path)
        print(f"Model loaded: {self.model_path}")

    def predict(self, image_path, conf=0.25):
        """Run YOLO inference and return detections with counts"""
        if self.model is None:
            return {"error": "Model not loaded"}

        results = self.model(image_path, conf=conf, verbose=False)[0]

        # Count by class
        bee_count = 0
        hornet_count = 0
        detections = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()

            if cls_id == 0:
                bee_count += 1
            elif cls_id == 1:
                hornet_count += 1

            detections.append({
                "class": self.classes.get(cls_id, "unknown"),
                "confidence": round(conf, 3),
                "bbox": [round(x, 1) for x in xyxy]
            })

        return {
            "bee_count": bee_count,
            "hornet_count": hornet_count,
            "total_detections": len(detections),
            "detections": detections
        }

    def visualize(self, image_path, output_path=None, conf=0.25):
        """Run inference and save/show image with bounding boxes"""
        if self.model is None:
            return None

        results = self.model(image_path, conf=conf, verbose=False)[0]
        img_with_boxes = results.plot()

        if output_path:
            cv2.imwrite(output_path, img_with_boxes)
            print(f"Saved: {output_path}")

        return img_with_boxes

    def to_sensor_data(self, prediction, ruche_id=1):
        """
        Convert prediction to SensorData format.
        Matches the backend model exactly.
        """
        bee_count = prediction.get("bee_count", 0)
        hornet_count = prediction.get("hornet_count", 0)

        # Determine bee state based on counts
        if hornet_count > 3:
            etat_abeilles = "stressed"
        elif hornet_count > 0:
            etat_abeilles = "agitated"
        elif bee_count > 200:
            etat_abeilles = "active"
        else:
            etat_abeilles = "normal"

        # Determine acoustic state
        if hornet_count > 2:
            etat_acoustique = "alert"
        elif hornet_count > 0:
            etat_acoustique = "loud"
        else:
            etat_acoustique = "normal"

        return {
            "ruche_id": ruche_id,
            "nombre_frelons": hornet_count,
            "nombre_abeilles_entrees": bee_count,
            "nombre_abeilles_sorties": 0,
            "temperature": 0.0,
            "humidite": 0.0,
            "etat_abeilles": etat_abeilles,
            "etat_acoustique": etat_acoustique
        }


def main():
    parser = argparse.ArgumentParser(description="BeeGuardAI - YOLO Detection")
    parser.add_argument("--image", type=str, help="Path to single image")
    parser.add_argument("--folder", type=str, help="Path to folder of images")
    parser.add_argument("--model", type=str,
                        default="models/bee_hornet_detector/weights/best.pt",
                        help="Path to YOLO model")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--ruche-id", type=int, default=1, help="Ruche ID for output")
    parser.add_argument("--visualize", action="store_true", help="Save images with boxes")
    parser.add_argument("--output", type=str, help="Output JSON file")

    args = parser.parse_args()

    if not args.image and not args.folder:
        print("Usage: python inference.py --image path/to/image.jpg")
        print("       python inference.py --folder path/to/images/")
        print("       python inference.py --image img.jpg --visualize")
        return

    detector = BeeHornetDetector(model_path=args.model)
    results = []

    if args.image:
        print(f"\nProcessing: {args.image}")
        prediction = detector.predict(args.image, conf=args.conf)
        sensor_data = detector.to_sensor_data(prediction, args.ruche_id)

        print("\n--- Detection Results ---")
        print(f"Bees: {prediction['bee_count']}")
        print(f"Hornets: {prediction['hornet_count']}")
        print(f"Total: {prediction['total_detections']}")

        print("\n--- SensorData Format ---")
        print(json.dumps(sensor_data, indent=2))

        if args.visualize:
            out_path = Path(args.image).stem + "_detected.jpg"
            detector.visualize(args.image, out_path, conf=args.conf)

        results.append(sensor_data)

    elif args.folder:
        folder = Path(args.folder)
        image_files = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))
        out_folder = Path("outputs/detections")

        if args.visualize:
            out_folder.mkdir(parents=True, exist_ok=True)

        print(f"\nProcessing {len(image_files)} images...")

        for img_path in image_files:
            prediction = detector.predict(str(img_path), conf=args.conf)
            sensor_data = detector.to_sensor_data(prediction, args.ruche_id)

            results.append({
                "image": img_path.name,
                **sensor_data
            })

            status = ""
            if prediction["hornet_count"] > 0:
                status = " [HORNET ALERT!]"

            print(f"  {img_path.name}: {prediction['bee_count']} bees, "
                  f"{prediction['hornet_count']} hornets{status}")

            if args.visualize:
                out_path = out_folder / f"{img_path.stem}_detected.jpg"
                detector.visualize(str(img_path), str(out_path), conf=args.conf)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()

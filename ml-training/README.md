# BeeGuardAI - ML Training (YOLO)

Train YOLOv8 to detect bees and hornets, outputs counts compatible with the backend SensorData format.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get a dataset (see below)

# 3. Train
python train.py

# 4. Run inference
python inference.py --image test.jpg --visualize
```

## Dataset Setup

Download a bee/hornet dataset from [Roboflow Universe](https://universe.roboflow.com/search?q=bee) and export as **YOLOv8** format.

Expected structure:
```
ml-training/
  data/
    train/
      images/    <- .jpg files
      labels/    <- .txt files (YOLO format)
    val/
      images/
      labels/
  config.yaml    <- points to data folders
```

### YOLO Label Format
Each `.txt` file has one line per object:
```
class x_center y_center width height
```
- class 0 = bee
- class 1 = hornet
- coordinates are normalized (0-1)

## Training

```bash
# Default (YOLOv8 nano, 100 epochs)
python train.py

# Faster training with smaller model
python train.py --model yolov8n --epochs 50

# Better accuracy with larger model
python train.py --model yolov8s --epochs 100
```

Models are saved to `models/bee_hornet_detector/weights/best.pt`

## Inference

```bash
# Single image
python inference.py --image path/to/image.jpg

# With bounding box visualization
python inference.py --image path/to/image.jpg --visualize

# Folder of images
python inference.py --folder path/to/images/ --output results.json
```

## Output Format

Matches the backend `SensorData` model:
```json
{
  "ruche_id": 1,
  "nombre_frelons": 2,
  "nombre_abeilles_entrees": 45,
  "nombre_abeilles_sorties": 0,
  "temperature": 0.0,
  "humidite": 0.0,
  "etat_abeilles": "agitated",
  "etat_acoustique": "loud"
}
```

## Model Sizes

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| yolov8n | 6MB | Fast | Good |
| yolov8s | 22MB | Medium | Better |
| yolov8m | 50MB | Slow | Best |

For ESP32/embedded, use `yolov8n` and export to TFLite after training.

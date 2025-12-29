from ultralytics import YOLO
import os

# Load YOLO model ONCE
MODEL_PATH = os.path.join("ml", "food_yolo.pt")
model = YOLO(MODEL_PATH)

def predict_foods(image_path):
    """
    Returns list of detected food class names.
    Example: ['carrot', 'beans']
    """
    results = model(image_path)
    result = results[0]

    # No detection
    if result.boxes is None or len(result.boxes) == 0:
        return []

    class_ids = result.boxes.cls.tolist()
    foods = []

    for cid in class_ids:
        name = result.names[int(cid)]
        foods.append(name)

    # remove duplicates
    return list(set(foods))

import io
import os
import time
import logging
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from PIL import Image
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yolo_service")

app = FastAPI(title="YOLOv11s P&ID Symbol Detector")

# Prioritize fine-tuned P&ID weights over baseline COCO weights
CUSTOM_WEIGHTS = Path("infra/models/pid_yolo_best.pt")
BASE_WEIGHTS = Path("models/yolo11s.pt")

if CUSTOM_WEIGHTS.exists() and CUSTOM_WEIGHTS.stat().st_size > 1024 * 1024:
    model_path = str(CUSTOM_WEIGHTS)
elif BASE_WEIGHTS.exists() and BASE_WEIGHTS.stat().st_size > 1024 * 1024:
    model_path = str(BASE_WEIGHTS)
else:
    model_path = "yolo11s.pt"

logger.info(f"Initializing YOLOv11s service with: {model_path}")
model = YOLO(model_path)

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "YOLOv11s P&ID Symbol Detector",
        "active_weights": model_path,
        "classes": model.names
    }

@app.post("/detect")
async def detect(file: UploadFile = File(None), image_path: str = Form(None)):
    start_time = time.time()
    
    if file:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    elif image_path:
        image = Image.open(image_path).convert("RGB")
    else:
        raise HTTPException(status_code=400, detail="Provide image file or image_path")

    width, height = image.size

    # Run inference at diagram resolution with balanced threshold (0.15)
    results = model(image, imgsz=1024, conf=0.15)
    
    detections = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label_name = model.names.get(cls_id, str(cls_id))
            conf = float(box.conf[0])
            xyxy = [float(coord) for coord in box.xyxy[0]]

            bbox_norm = {
                "x_center": round(((xyxy[0] + xyxy[2]) / 2.0) / width, 4),
                "y_center": round(((xyxy[1] + xyxy[3]) / 2.0) / height, 4),
                "width": round((xyxy[2] - xyxy[0]) / width, 4),
                "height": round((xyxy[3] - xyxy[1]) / height, 4),
            }

            detections.append({
                "class_id": cls_id,
                "label": label_name,
                "confidence": round(conf, 3),
                "box": [round(c, 2) for c in xyxy],
                "normalized_box": [
                    round(xyxy[1] / height, 4),  # ymin
                    round(xyxy[0] / width, 4),   # xmin
                    round(xyxy[3] / height, 4),  # ymax
                    round(xyxy[2] / width, 4),   # xmax
                ],
                "bbox_normalized": bbox_norm
            })

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "status": "success",
        "model": model_path,
        "latency_ms": round(elapsed_ms, 2),
        "total_detections": len(detections),
        "detections_count": len(detections),
        "image_dimensions": {"width": width, "height": height},
        "detections": detections
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)

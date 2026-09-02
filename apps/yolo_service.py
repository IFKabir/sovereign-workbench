import time
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yolo_service")

app = FastAPI(title="YOLOv11s P&ID Detection Service")

def load_yolo_model():
    candidates = [
        Path("infra/models/pid_yolo_best.pt"),
        Path("training/yolo-pid/weights/best.pt"),
        Path("yolov8s.pt"),
        Path("yolov11s.pt"),
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.stat().st_size > 1024 * 1024:
            try:
                logger.info(f"Attempting to load YOLO model from {candidate}...")
                m = YOLO(str(candidate))
                logger.info(f"Successfully loaded YOLO model from {candidate}")
                return m, candidate
            except Exception as e:
                logger.warning(f"Could not load model weights from {candidate}: {e}")

    logger.info("Loading default base Ultralytics model 'yolov8s.pt'...")
    m = YOLO("yolov8s.pt")
    return m, Path("yolov8s.pt")

model, model_file = load_yolo_model()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "YOLOv11s P&ID Detector",
        "model": str(model_file)
    }

@app.post("/detect")
async def detect(file: UploadFile = File(None), image_path: str = Form(None)):
    start_time = time.time()
    source = None

    if file:
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        source = str(temp_path)
    elif image_path:
        source = image_path
    else:
        raise HTTPException(status_code=400, detail="Provide image file or image_path")

    results = model.predict(source, verbose=False)
    boxes = []
    
    for r in results:
        for b in r.boxes:
            box_data = b.xywhn[0].tolist() if hasattr(b, 'xywhn') else [0, 0, 0, 0]
            cls_id = int(b.cls[0])
            cls_name = model.names.get(cls_id, str(cls_id))
            conf = float(b.conf[0])
            boxes.append({
                "class_id": cls_id,
                "label": cls_name,
                "confidence": conf,
                "bbox_normalized": {
                    "x_center": box_data[0],
                    "y_center": box_data[1],
                    "width": box_data[2],
                    "height": box_data[3]
                }
            })

    elapsed_ms = (time.time() - start_time) * 1000
    return {
        "status": "success",
        "latency_ms": round(elapsed_ms, 2),
        "detections_count": len(boxes),
        "detections": boxes
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

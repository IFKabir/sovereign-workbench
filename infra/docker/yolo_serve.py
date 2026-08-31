"""YOLOv11s P&ID Symbol Detection Microservice.

Serves the fine-tuned YOLOv11s model for detecting symbols in
Piping & Instrumentation Diagrams (P&IDs) via a simple REST API.
Designed for sovereign, air-gapped deployment.
"""
import os
import io
import time
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from ultralytics import YOLO

app = FastAPI(title="P&ID Symbol Detector", version="0.1.0")

model_path = os.environ.get("YOLO_MODEL_PATH", "/models/best.pt")
model = None

@app.on_event("startup")
async def load_model():
    global model
    if os.path.exists(model_path):
        model = YOLO(model_path)
    else:
        print(f"WARNING: Model not found at {model_path}, using default YOLOv11s")
        model = YOLO("yolo11s.pt")

@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": model is not None, "model_path": model_path}

@app.post("/detect")
async def detect_symbols(file: UploadFile = File(...), confidence: float = 0.25):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    start = time.time()
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    results = model(image, conf=confidence)
    
    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "x_min": float(box.xyxy[0][0]),
                "y_min": float(box.xyxy[0][1]),
                "x_max": float(box.xyxy[0][2]),
                "y_max": float(box.xyxy[0][3]),
                "confidence": float(box.conf[0]),
                "label": r.names[int(box.cls[0])],
                "class_id": int(box.cls[0]),
            })
    
    processing_time = (time.time() - start) * 1000
    
    return JSONResponse({
        "detections": detections,
        "total_symbols": len(detections),
        "processing_time_ms": round(processing_time, 2),
        "image_size": {"width": image.width, "height": image.height},
        "model_version": "yolov11s-pidcon",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

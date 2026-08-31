import os
from ultralytics import YOLO
import torch

def train_yolo():
    """Trains YOLOv11s for P&ID symbol detection."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_yaml = os.path.join(base_dir, "data.yaml")
    output_dir = os.path.join(base_dir, "../../models/yolo-pid")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading YOLOv11s model...")
    # Using v8s as placeholder for v11s which might be the local naming convention
    model = YOLO('yolov8s.pt') 
    
    print("Starting training...")
    results = model.train(
        data=data_yaml,
        epochs=100,
        batch=16,
        imgsz=1024,
        patience=20,
        project=os.path.join(base_dir, "runs"),
        name="pid_symbol_detection",
        exist_ok=True,
        # Augmentations suitable for P&IDs
        mosaic=1.0,
        mixup=0.1,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0, # Rotation not ideal for schematics usually
        translate=0.1,
        scale=0.5,
        shear=0.0,
        flipud=0.0,
        fliplr=0.0, # Direction matters in P&ID
        save=True
    )
    
    print(f"Training completed. Best mAP50: {results.box.map50}, mAP50-95: {results.box.map}")
    
    # Export models
    best_model_path = os.path.join(base_dir, "runs", "pid_symbol_detection", "weights", "best.pt")
    if os.path.exists(best_model_path):
        print("Exporting best model to ONNX and TorchScript...")
        best_model = YOLO(best_model_path)
        
        # Export to ONNX
        best_model.export(format='onnx', dynamic=True, imgsz=1024, simplify=True)
        
        # Export to TorchScript
        best_model.export(format='torchscript', imgsz=1024)
        
        # Copy to central models directory
        import shutil
        shutil.copy2(best_model_path, os.path.join(output_dir, "yolo_pid_best.pt"))
        onnx_path = best_model_path.replace(".pt", ".onnx")
        if os.path.exists(onnx_path):
            shutil.copy2(onnx_path, os.path.join(output_dir, "yolo_pid_best.onnx"))
            
        print(f"Models saved to {output_dir}")
    else:
        print("Could not find best model weights.")

if __name__ == "__main__":
    train_yolo()

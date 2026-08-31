import os
import json
import random
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET

CLASSES = [
    "valve", "pump", "compressor", "heat_exchanger", "reactor", 
    "column", "tank", "instrument", "control_valve", "safety_valve", 
    "orifice_plate", "flow_meter", "pressure_gauge", "temperature_sensor", 
    "level_indicator", "motor", "filter", "mixer"
]
CLASS2ID = {c: i for i, c in enumerate(CLASSES)}

def convert_voc_xml_to_yolo(xml_path: str, img_width: int, img_height: int) -> List[str]:
    """Converts a VOC XML annotation file to YOLO format strings."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    yolo_annotations = []
    
    for obj in root.findall('object'):
        name = obj.find('name').text.lower()
        if name not in CLASS2ID:
            continue
            
        class_id = CLASS2ID[name]
        bndbox = obj.find('bndbox')
        
        xmin = float(bndbox.find('xmin').text)
        ymin = float(bndbox.find('ymin').text)
        xmax = float(bndbox.find('xmax').text)
        ymax = float(bndbox.find('ymax').text)
        
        # Convert to YOLO format (normalized center_x, center_y, width, height)
        x_center = ((xmin + xmax) / 2) / img_width
        y_center = ((ymin + ymax) / 2) / img_height
        width = (xmax - xmin) / img_width
        height = (ymax - ymin) / img_height
        
        # Ensure values are within [0, 1]
        x_center = max(0.0, min(1.0, x_center))
        y_center = max(0.0, min(1.0, y_center))
        width = max(0.0, min(1.0, width))
        height = max(0.0, min(1.0, height))
        
        yolo_annotations.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
        
    return yolo_annotations

def create_dataset_split(
    image_paths: List[str], 
    xml_paths_dict: Dict[str, str],
    output_dir: str
):
    """Creates train/val/test splits and copies/symlinks files."""
    random.seed(42)
    random.shuffle(image_paths)
    
    n = len(image_paths)
    train_idx = int(n * 0.7)
    val_idx = int(n * 0.9)
    
    splits = {
        "train": image_paths[:train_idx],
        "val": image_paths[train_idx:val_idx],
        "test": image_paths[val_idx:]
    }
    
    stats = {"train": 0, "val": 0, "test": 0}
    
    for split_name, paths in splits.items():
        split_img_dir = os.path.join(output_dir, "images", split_name)
        split_lbl_dir = os.path.join(output_dir, "labels", split_name)
        os.makedirs(split_img_dir, exist_ok=True)
        os.makedirs(split_lbl_dir, exist_ok=True)
        
        for img_path in paths:
            img_name = os.path.basename(img_path)
            base_name = os.path.splitext(img_name)[0]
            
            if base_name in xml_paths_dict:
                xml_path = xml_paths_dict[base_name]
                
                # Copy image (using copy instead of symlink for portability)
                dst_img = os.path.join(split_img_dir, img_name)
                if not os.path.exists(dst_img):
                    shutil.copy2(img_path, dst_img)
                    
                # Convert and save labels
                # Dummy image dimensions, ideally extract from image or XML
                # Assuming XML has size element
                try:
                    tree = ET.parse(xml_path)
                    size = tree.getroot().find('size')
                    w = int(size.find('width').text)
                    h = int(size.find('height').text)
                except:
                    # Fallback default size if not found
                    w, h = 1024, 1024
                    
                yolo_labels = convert_voc_xml_to_yolo(xml_path, w, h)
                
                label_path = os.path.join(split_lbl_dir, f"{base_name}.txt")
                with open(label_path, 'w') as f:
                    f.write('\n'.join(yolo_labels))
                    
                stats[split_name] += 1
                
    return stats

def main():
    """Main execution function."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths (dummy paths for the example, would need to point to actual PIDCon dataset)
    input_dir = os.path.join(base_dir, "PIDCon_raw")
    output_dir = os.path.join(base_dir, "pid_yolo_dataset")
    
    # We create dummy raw data for the script to run without errors
    os.makedirs(os.path.join(input_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(input_dir, "annotations"), exist_ok=True)
    
    print(f"Scanning {input_dir} for dataset...")
    # In a real scenario, we'd read actual files. Here we just prepare the structure.
    
    # Create data.yaml
    yaml_data = {
        "path": output_dir,
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {i: name for i, name in enumerate(CLASSES)}
    }
    
    yaml_path = os.path.join(base_dir, "data.yaml")
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False)
        
    print(f"Created data.yaml at {yaml_path}")
    print("Dataset conversion script ready. Point to actual PIDCon directory to convert.")

if __name__ == "__main__":
    main()

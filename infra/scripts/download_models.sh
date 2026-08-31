#!/bin/bash
set -e

# Default models directory
MODELS_DIR="${1:-/home/ifkabir/work/sih/sovereign-workbench/models}"
mkdir -p "$MODELS_DIR"

echo "=== Downloading models to $MODELS_DIR ==="

# Check for huggingface-cli
if ! command -v huggingface-cli &> /dev/null; then
    echo "huggingface-cli not found. Installing via pip..."
    pip install -U "huggingface_hub[cli]"
fi

# Qwen2.5-VL-7B-Instruct
echo "Downloading Qwen2.5-VL-7B-Instruct..."
huggingface-cli download Qwen/Qwen2.5-VL-7B-Instruct --local-dir "$MODELS_DIR/Qwen2.5-VL-7B-Instruct"

# BGE-M3 embeddings
echo "Downloading BGE-M3 embeddings..."
huggingface-cli download BAAI/bge-m3 --local-dir "$MODELS_DIR/bge-m3"

# BGE-Reranker-Large
echo "Downloading BGE-Reranker-Large..."
huggingface-cli download BAAI/bge-reranker-large --local-dir "$MODELS_DIR/bge-reranker-large"

# ModernBERT-base
echo "Downloading ModernBERT-base..."
huggingface-cli download answerdotai/ModernBERT-base --local-dir "$MODELS_DIR/ModernBERT-base"

# YOLOv11s base weights
echo "Downloading YOLOv11s base weights..."
if [ ! -f "$MODELS_DIR/yolo11s.pt" ]; then
    wget -q --show-progress -O "$MODELS_DIR/yolo11s.pt" https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt
else
    echo "yolo11s.pt already exists."
fi

echo "=== Model downloads complete! ==="

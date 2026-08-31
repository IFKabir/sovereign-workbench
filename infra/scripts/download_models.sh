#!/bin/bash
# =============================================================================
# Sovereign Workbench — Model Download Script
# =============================================================================
# Downloads all required model weights for local, air-gapped operation.
# Run this BEFORE sealing the air-gap (docker-compose.airgap.yml).
#
# Usage:
#   bash infra/scripts/download_models.sh [MODELS_DIR]
#
# Models downloaded:
#   1. ModernBERT-base      — task router backbone (~600MB)
#   2. BGE-M3               — embedding model (~2.3GB)
#   3. BGE-Reranker-Large   — reranker (~1.3GB)
#   4. YOLOv11s             — object detection base weights (~19MB)
#   5. Qwen2.5-VL-7B Q4     — quantized VLM for 6GB GPUs (~4.8GB)
#
# SIH26117 · MRPL · Zero Network Egress after download
# =============================================================================
set -euo pipefail

MODELS_DIR="${1:-$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")")/models}"
VENV_PYTHON="$(dirname "$(dirname "$(dirname "$(readlink -f "$0")")")")/.venv/bin/python"

# Fall back to system python if venv doesn't exist
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python3"
fi

mkdir -p "$MODELS_DIR"
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Sovereign Workbench — Model Download Script        ║"
echo "║  Target: $MODELS_DIR"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# --------------------------------------------------------------------------
# 1. ModernBERT-base (task router fine-tuning backbone)
# --------------------------------------------------------------------------
if [ -d "$MODELS_DIR/ModernBERT-base" ] && [ -f "$MODELS_DIR/ModernBERT-base/config.json" ]; then
    echo "✅ ModernBERT-base already exists, skipping."
else
    echo "⬇️  Downloading ModernBERT-base..."
    $VENV_PYTHON -c "
from huggingface_hub import snapshot_download
snapshot_download('answerdotai/ModernBERT-base', local_dir='$MODELS_DIR/ModernBERT-base')
print('✅ ModernBERT-base downloaded')
"
fi
echo ""

# --------------------------------------------------------------------------
# 2. BGE-M3 embeddings
# --------------------------------------------------------------------------
if [ -d "$MODELS_DIR/bge-m3" ] && [ -f "$MODELS_DIR/bge-m3/config.json" ]; then
    echo "✅ BGE-M3 already exists, skipping."
else
    echo "⬇️  Downloading BGE-M3 embeddings (~2.3GB)..."
    $VENV_PYTHON -c "
from huggingface_hub import snapshot_download
snapshot_download('BAAI/bge-m3', local_dir='$MODELS_DIR/bge-m3')
print('✅ BGE-M3 downloaded')
"
fi
echo ""

# --------------------------------------------------------------------------
# 3. BGE-Reranker-Large
# --------------------------------------------------------------------------
if [ -d "$MODELS_DIR/bge-reranker-large" ] && [ -f "$MODELS_DIR/bge-reranker-large/config.json" ]; then
    echo "✅ BGE-Reranker-Large already exists, skipping."
else
    echo "⬇️  Downloading BGE-Reranker-Large (~1.3GB)..."
    $VENV_PYTHON -c "
from huggingface_hub import snapshot_download
snapshot_download('BAAI/bge-reranker-large', local_dir='$MODELS_DIR/bge-reranker-large')
print('✅ BGE-Reranker-Large downloaded')
"
fi
echo ""

# --------------------------------------------------------------------------
# 4. YOLOv11s base weights
# --------------------------------------------------------------------------
if [ -f "$MODELS_DIR/yolo11s.pt" ]; then
    echo "✅ YOLOv11s weights already exist, skipping."
else
    echo "⬇️  Downloading YOLOv11s base weights..."
    wget -q --show-progress -O "$MODELS_DIR/yolo11s.pt" \
        "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt"
    echo "✅ YOLOv11s downloaded"
fi
echo ""

# --------------------------------------------------------------------------
# 5. Qwen2.5-VL-7B-Instruct (GGUF Q4_K_M quantization for 6GB GPUs)
# --------------------------------------------------------------------------
if [ -f "$MODELS_DIR/qwen2.5-vl-7b-instruct-q4_k_m.gguf" ]; then
    echo "✅ Qwen2.5-VL GGUF already exists, skipping."
else
    echo "⬇️  Downloading Qwen2.5-VL-7B Q4_K_M GGUF (~4.8GB)..."
    echo "   (This is the quantized version that fits in 6GB VRAM)"
    $VENV_PYTHON -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    'Qwen/Qwen2.5-VL-7B-Instruct-GGUF',
    filename='qwen2.5-vl-7b-instruct-q4_k_m.gguf',
    local_dir='$MODELS_DIR',
)
print('✅ Qwen2.5-VL GGUF downloaded')
" 2>&1 || {
        echo "⚠️  GGUF download failed. Trying full-precision snapshot..."
        echo "   NOTE: Full model requires ~16GB VRAM, may not fit on RTX 4050"
        $VENV_PYTHON -c "
from huggingface_hub import snapshot_download
snapshot_download('Qwen/Qwen2.5-VL-7B-Instruct', local_dir='$MODELS_DIR/Qwen2.5-VL-7B-Instruct')
print('✅ Qwen2.5-VL full-precision downloaded')
"
    }
fi
echo ""

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Download Summary                                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "Models directory: $MODELS_DIR"
echo ""
du -sh "$MODELS_DIR"/* 2>/dev/null || echo "(empty)"
echo ""
echo "Total size:"
du -sh "$MODELS_DIR"
echo ""
echo "✅ All model downloads complete."
echo "   You can now seal the air-gap with:"
echo "   docker compose -f infra/docker/docker-compose.airgap.yml up --build"

#!/usr/bin/env bash
# ==============================================================================
# Sovereign AI Workbench — Unified Model Training Pipeline Master Orchestrator
# SIH26117 · MRPL · Smart Automation
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║   Sovereign AI Workbench — Offline Model Training Pipeline       ║"
echo "║   Track A: YOLOv11s P&ID Symbol Detector                         ║"
echo "║   Track B: Qwen2.5-VL-7B Multimodal QLoRA Fine-Tuning             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# ------------------------------------------------------------------------------
# STEP 1: Track A — YOLO Dataset Conversion
# ------------------------------------------------------------------------------
echo "============================================================"
echo "  STEP 1: Converting P&ID Annotations to ISA-5.1 YOLO Format"
echo "============================================================"
python training/yolo-pid/convert_datasets.py
echo "  ✅ STEP 1 COMPLETE: P&ID Dataset converted into 80/20 train/val split."
echo ""

# ------------------------------------------------------------------------------
# STEP 2: Track A — YOLOv11s Micro-Symbol Training
# ------------------------------------------------------------------------------
echo "============================================================"
echo "  STEP 2: Fine-Tuning YOLOv11s Micro-Symbol Detector"
echo "============================================================"
python training/yolo-pid/train_yolo.py
echo "  ✅ STEP 2 COMPLETE: YOLOv11s weights saved to training/yolo-pid/weights/best.pt"
echo ""

# ------------------------------------------------------------------------------
# STEP 3: Track B — Visual Instruction Dataset Preparation
# ------------------------------------------------------------------------------
echo "============================================================"
echo "  STEP 3: Aggregating 30+ Source Instruction Dataset"
echo "============================================================"
python training/vlm-finetuning/build_instruction_dataset.py
echo "  ✅ STEP 3 COMPLETE: Sovereign VLM instruction dataset built."
echo ""

# ------------------------------------------------------------------------------
# STEP 4: Track B — Qwen2.5-VL-7B QLoRA Fine-Tuning
# ------------------------------------------------------------------------------
echo "============================================================"
echo "  STEP 4: QLoRA Fine-Tuning Qwen2.5-VL-7B Multimodal Backbone"
echo "============================================================"
python training/vlm-finetuning/train_qwen2_5_vl.py
echo "  ✅ STEP 4 COMPLETE: QLoRA Adapters saved to training/vlm-finetuning/adapters/best_lora_weights/"
echo ""

echo "============================================================"
echo "  TRAINING PIPELINE SUMMARY"
echo "============================================================"
echo "  YOLO Weights: training/yolo-pid/weights/best.pt"
echo "  YOLO ONNX:    training/yolo-pid/weights/best.onnx"
echo "  VLM Adapters: training/vlm-finetuning/adapters/best_lora_weights/"
echo "  Status:       ALL TRAINING STAGES COMPLETED SUCCESSFULLY (100%)"
echo "============================================================"

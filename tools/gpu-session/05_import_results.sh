#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  STEP 6: Import fine-tuned results back to your laptop
#  Run this BACK on your laptop after the GPU session
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PENDRIVE="${1:-/media/ifkabir/PENDRIVE}"
RESULTS_DIR="$PENDRIVE/sovereign-results"
WORK_DIR="/home/ifkabir/work/sih/sovereign-workbench"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SOVEREIGN WORKBENCH — IMPORT FINE-TUNED RESULTS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ ! -d "$RESULTS_DIR" ]; then
    echo "Results not found at $RESULTS_DIR"
    echo "Usage: $0 /path/to/pendrive"
    exit 1
fi

# 1. Import YOLO weights
echo -e "${GREEN}[1/4] Importing YOLO weights...${NC}"
if [ -d "$RESULTS_DIR/yolo-weights" ]; then
    cp -v "$RESULTS_DIR/yolo-weights/"*.pt "$WORK_DIR/infra/models/" 2>/dev/null || true
    echo -e "  ✅ YOLO weights imported"
fi

# 2. Import LLM LoRA adapter
echo -e "\n${GREEN}[2/4] Importing LLM LoRA adapter...${NC}"
if [ -d "$RESULTS_DIR/llm-lora-adapter" ]; then
    rsync -av "$RESULTS_DIR/llm-lora-adapter/" "$WORK_DIR/infra/models/qwen2.5-7b-industrial-lora/"
    echo -e "  ✅ LLM adapter imported"
fi

# 3. Import VLM LoRA adapter
echo -e "\n${GREEN}[3/4] Importing VLM LoRA adapter...${NC}"
if [ -d "$RESULTS_DIR/vlm-lora-adapter" ]; then
    rsync -av "$RESULTS_DIR/vlm-lora-adapter/" "$WORK_DIR/infra/models/qwen2.5-vl-industrial-lora/"
    echo -e "  ✅ VLM adapter imported"
fi

# 4. Import screenshots
echo -e "\n${GREEN}[4/4] Importing screenshots...${NC}"
if [ -d "$RESULTS_DIR/screenshots" ]; then
    cp -r "$RESULTS_DIR/screenshots/" "$WORK_DIR/presentation-screenshots/"
    echo -e "  ✅ $(ls -1 "$WORK_DIR/presentation-screenshots/"*.png 2>/dev/null | wc -l) screenshots imported"
fi

echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ ALL RESULTS IMPORTED${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Fine-tuned weights in: $WORK_DIR/infra/models/"
echo -e "Screenshots in: $WORK_DIR/presentation-screenshots/"
echo ""
echo -e "${YELLOW}Update .env to use fine-tuned LLM on your laptop:${NC}"
echo -e "  The LoRA adapter requires the base Qwen2.5-7B model."
echo -e "  On your 6GB GPU, continue using Qwen2.5-0.5B for inference."
echo -e "  The fine-tuned weights are for the 24GB GPU demo only."

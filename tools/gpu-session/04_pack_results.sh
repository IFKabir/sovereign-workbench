#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  STEP 5: Pack results back to pendrive to bring home
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

WORK_DIR="${WORK_DIR:-$HOME/sovereign-workbench}"
PENDRIVE="${1:-/media/$USER/PENDRIVE}"
DEST="$PENDRIVE/sovereign-results"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SOVEREIGN WORKBENCH — PACK RESULTS TO PENDRIVE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ ! -d "$PENDRIVE" ]; then
    echo -e "Usage: $0 /path/to/pendrive"
    exit 1
fi

mkdir -p "$DEST"

# 1. Fine-tuned YOLO weights
echo -e "${GREEN}[1/5] Packing fine-tuned YOLO weights...${NC}"
mkdir -p "$DEST/yolo-weights"
cp -v "$WORK_DIR/infra/models/pid_yolo_best.pt" "$DEST/yolo-weights/" 2>/dev/null || true
cp -v "$WORK_DIR/infra/models/pid_yolo11s_best.pt" "$DEST/yolo-weights/" 2>/dev/null || true
cp -v "$WORK_DIR/infra/models/pid_yolo11m_best.pt" "$DEST/yolo-weights/" 2>/dev/null || true
cp -v "$WORK_DIR/infra/models/pid_yolo11l_best.pt" "$DEST/yolo-weights/" 2>/dev/null || true

# Copy YOLO training curves/results
cp -r "$WORK_DIR/training/yolo-pid/runs/" "$DEST/yolo-training-runs/" 2>/dev/null || true

# 2. Fine-tuned LLM LoRA adapter
echo -e "\n${GREEN}[2/5] Packing LLM LoRA adapter...${NC}"
if [ -d "$WORK_DIR/infra/models/qwen2.5-7b-industrial-lora" ]; then
    rsync -av "$WORK_DIR/infra/models/qwen2.5-7b-industrial-lora/" "$DEST/llm-lora-adapter/"
    echo -e "  ✅ LLM adapter packed"
fi

# 3. Fine-tuned VLM LoRA adapter
echo -e "\n${GREEN}[3/5] Packing VLM LoRA adapter...${NC}"
if [ -d "$WORK_DIR/infra/models/qwen2.5-vl-industrial-lora" ]; then
    rsync -av "$WORK_DIR/infra/models/qwen2.5-vl-industrial-lora/" "$DEST/vlm-lora-adapter/"
    echo -e "  ✅ VLM adapter packed"
fi

# 4. Screenshots
echo -e "\n${GREEN}[4/5] Packing presentation screenshots...${NC}"
if [ -d "$WORK_DIR/presentation-screenshots" ]; then
    cp -r "$WORK_DIR/presentation-screenshots/" "$DEST/screenshots/"
    echo -e "  ✅ $(ls -1 "$DEST/screenshots/"*.png 2>/dev/null | wc -l) screenshots packed"
fi

# 5. Logs & benchmark results
echo -e "\n${GREEN}[5/5] Packing logs & benchmark results...${NC}"
mkdir -p "$DEST/logs"
cp "$WORK_DIR/logs/"*.log "$DEST/logs/" 2>/dev/null || true
cp -r "$WORK_DIR/tools/benchmark/results/" "$DEST/benchmark-results/" 2>/dev/null || true

echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ ALL RESULTS PACKED${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Contents:"
du -sh "$DEST"/*/ 2>/dev/null
echo ""
echo -e "Total: $(du -sh "$DEST" | cut -f1)"
echo ""
echo -e "${YELLOW}Take the pendrive back to your laptop and run:${NC}"
echo -e "  bash tools/gpu-session/05_import_results.sh /path/to/pendrive"

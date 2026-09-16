#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  STEP 3: Fine-tune ALL models on the 24GB GPU
#  Run after 01_setup_remote.sh
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

WORK_DIR="${WORK_DIR:-$HOME/sovereign-workbench}"
cd "$WORK_DIR"
source .venv/bin/activate

mkdir -p logs

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SOVEREIGN WORKBENCH — FINE-TUNING SUITE (24GB GPU)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo ""

TOTAL_START=$(date +%s)

# ═══════════════════════════════════════════════════════════════════
#  PHASE 1: YOLO P&ID Fine-tuning (~30-45 min)
# ═══════════════════════════════════════════════════════════════════
echo -e "\n${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  PHASE 1: YOLO P&ID Symbol Detection Fine-tuning ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"

YOLO_MODELS=("yolo11s.pt" "yolo11m.pt" "yolo11l.pt")
YOLO_YAML="$WORK_DIR/training/yolo-pid/pid_data.yaml"

for yolo_base in "${YOLO_MODELS[@]}"; do
    name="${yolo_base%.pt}"
    echo -e "\n${GREEN}Training: $name on P&ID dataset...${NC}"

    python3 -c "
from ultralytics import YOLO
import os

model = YOLO('$yolo_base')
results = model.train(
    data='$YOLO_YAML',
    epochs=80,
    imgsz=1024,
    batch=16,
    workers=8,
    optimizer='AdamW',
    lr0=0.001,
    augment=True,
    fliplr=0.5,
    degrees=10.0,
    mosaic=0.8,
    project='$WORK_DIR/training/yolo-pid/runs',
    name='pid_$name',
    exist_ok=True,
    save=True,
    plots=True,
    patience=15,
)

# Export best weights
import shutil
best_w = '$WORK_DIR/training/yolo-pid/runs/pid_$name/weights/best.pt'
if os.path.exists(best_w):
    shutil.copy2(best_w, '$WORK_DIR/infra/models/pid_${name}_best.pt')
    print(f'Exported: pid_${name}_best.pt')
" 2>&1 | tee "logs/yolo_${name}.log"

    echo -e "  ${GREEN}✅ $name training complete${NC}"
done

# Pick the best YOLO weights based on validation mAP
echo -e "\n${GREEN}Selecting best YOLO model...${NC}"
python3 -c "
import os, csv
best_map, best_model = 0.0, ''
for name in ['yolo11s', 'yolo11m', 'yolo11l']:
    csv_path = f'training/yolo-pid/runs/pid_{name}/results.csv'
    if os.path.exists(csv_path):
        with open(csv_path) as f:
            rows = list(csv.DictReader(f))
            if rows:
                last = rows[-1]
                # mAP50 column
                for key in last:
                    if 'mAP50' in key and 'mAP50-95' not in key:
                        val = float(last[key].strip())
                        print(f'  {name}: mAP50={val:.4f}')
                        if val > best_map:
                            best_map = val
                            best_model = name
if best_model:
    import shutil
    src = f'infra/models/pid_{best_model}_best.pt'
    dst = 'infra/models/pid_yolo_best.pt'
    shutil.copy2(src, dst)
    print(f'  🏆 Best YOLO: {best_model} (mAP50={best_map:.4f}) → pid_yolo_best.pt')
"

# ═══════════════════════════════════════════════════════════════════
#  PHASE 2: LLM QLoRA Fine-tuning (~60-90 min)
# ═══════════════════════════════════════════════════════════════════
echo -e "\n${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  PHASE 2: LLM QLoRA Fine-tuning (Qwen2.5-7B)     ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"

python3 tools/gpu-session/finetune_llm.py 2>&1 | tee logs/llm_finetune.log

echo -e "  ${GREEN}✅ LLM fine-tuning complete${NC}"

# ═══════════════════════════════════════════════════════════════════
#  PHASE 3: VLM QLoRA Fine-tuning (~60-120 min)
# ═══════════════════════════════════════════════════════════════════
echo -e "\n${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  PHASE 3: VLM QLoRA Fine-tuning (Qwen2.5-VL-7B)  ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"

python3 tools/gpu-session/finetune_vlm.py 2>&1 | tee logs/vlm_finetune.log

echo -e "  ${GREEN}✅ VLM fine-tuning complete${NC}"

# ═══════════════════════════════════════════════════════════════════
TOTAL_END=$(date +%s)
ELAPSED=$(( (TOTAL_END - TOTAL_START) / 60 ))

echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ ALL FINE-TUNING COMPLETE (${ELAPSED} minutes total)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Fine-tuned weights saved to:"
echo -e "  YOLO: infra/models/pid_yolo_best.pt"
echo -e "  LLM:  infra/models/qwen2.5-7b-industrial-lora/"
echo -e "  VLM:  infra/models/qwen2.5-vl-industrial-lora/"
echo ""
echo -e "${YELLOW}NEXT: Capture presentation screenshots:${NC}"
echo -e "  bash tools/gpu-session/03_run_and_screenshot.sh"

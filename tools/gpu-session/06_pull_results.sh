#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  Pull fine-tuned results back from the GPU machine to this laptop
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

GPU_USER="${1:-}"
GPU_IP="${2:-}"

if [ -z "$GPU_USER" ] || [ -z "$GPU_IP" ]; then
    echo "Usage: $0 <gpu_username> <gpu_ip>"
    exit 1
fi

REMOTE="$GPU_USER@$GPU_IP"
REMOTE_DIR="/home/$GPU_USER/sovereign-workbench"
LOCAL_DIR="/home/ifkabir/work/sih/sovereign-workbench"

echo -e "${CYAN}  PULLING RESULTS FROM $REMOTE${NC}"

# Fine-tuned YOLO weights
echo -e "${GREEN}[1/4] Pulling YOLO weights...${NC}"
rsync -avz --progress "$REMOTE:$REMOTE_DIR/infra/models/pid_*" "$LOCAL_DIR/infra/models/" 2>/dev/null || true
rsync -avz --progress "$REMOTE:$REMOTE_DIR/training/yolo-pid/runs/" "$LOCAL_DIR/training/yolo-pid/runs/" 2>/dev/null || true

# LLM LoRA adapter
echo -e "\n${GREEN}[2/4] Pulling LLM LoRA adapter...${NC}"
rsync -avz --progress "$REMOTE:$REMOTE_DIR/infra/models/qwen2.5-7b-industrial-lora/" "$LOCAL_DIR/infra/models/qwen2.5-7b-industrial-lora/" 2>/dev/null || true

# VLM LoRA adapter
echo -e "\n${GREEN}[3/4] Pulling VLM LoRA adapter...${NC}"
rsync -avz --progress "$REMOTE:$REMOTE_DIR/infra/models/qwen2.5-vl-industrial-lora/" "$LOCAL_DIR/infra/models/qwen2.5-vl-industrial-lora/" 2>/dev/null || true

# Screenshots
echo -e "\n${GREEN}[4/4] Pulling screenshots...${NC}"
mkdir -p "$LOCAL_DIR/presentation-screenshots"
rsync -avz --progress "$REMOTE:$REMOTE_DIR/presentation-screenshots/" "$LOCAL_DIR/presentation-screenshots/" 2>/dev/null || true

echo -e "\n${GREEN}✅ All results pulled!${NC}"
echo -e "Screenshots: $LOCAL_DIR/presentation-screenshots/"
echo -e "YOLO weights: $LOCAL_DIR/infra/models/pid_yolo_best.pt"
ls -la "$LOCAL_DIR/presentation-screenshots/"*.png 2>/dev/null | wc -l | xargs -I{} echo -e "Total screenshots: {}"

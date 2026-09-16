#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  DIRECT PC-TO-PC TRANSFER (no pendrive needed)
#  Transfer code + models over SSH / local network
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# ─── Configuration ──────────────────────────────────────────────────────────
GPU_USER="${1:-}"
GPU_IP="${2:-}"

if [ -z "$GPU_USER" ] || [ -z "$GPU_IP" ]; then
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  SOVEREIGN WORKBENCH — DIRECT PC-TO-PC TRANSFER${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  $0 <gpu_username> <gpu_ip_address>"
    echo ""
    echo -e "${YELLOW}Example:${NC}"
    echo -e "  $0 student 192.168.1.50"
    echo -e "  $0 admin 10.0.0.5"
    echo ""
    echo -e "${YELLOW}How to find the GPU machine's IP:${NC}"
    echo -e "  On the GPU machine, run: ${GREEN}hostname -I | awk '{print \$1}'${NC}"
    echo -e "  Or: ${GREEN}ip addr show | grep 'inet ' | grep -v 127.0.0.1${NC}"
    echo ""
    echo -e "${YELLOW}Prerequisites on the GPU machine:${NC}"
    echo -e "  ${GREEN}sudo apt install openssh-server${NC}    # Enable SSH"
    echo -e "  ${GREEN}sudo systemctl start ssh${NC}            # Start SSH"
    echo ""
    echo -e "${YELLOW}If using direct ethernet cable:${NC}"
    echo -e "  On GPU machine: ${GREEN}sudo ip addr add 192.168.100.2/24 dev eth0${NC}"
    echo -e "  On this laptop:  ${GREEN}sudo ip addr add 192.168.100.1/24 dev eth0${NC}"
    echo -e "  Then run: $0 <user> 192.168.100.2"
    exit 1
fi

REMOTE="$GPU_USER@$GPU_IP"
REMOTE_DIR="/home/$GPU_USER/sovereign-workbench"
LOCAL_DIR="/home/ifkabir/work/sih/sovereign-workbench"
HF_CACHE="$HOME/.cache/huggingface/hub"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  DIRECT TRANSFER: This PC → $REMOTE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# ─── Test connection ─────────────────────────────────────────────────────────
echo -e "${GREEN}[0/5] Testing SSH connection...${NC}"
if ssh -o ConnectTimeout=5 -o BatchMode=yes "$REMOTE" "echo OK" 2>/dev/null; then
    echo -e "  ${GREEN}✅ SSH connection OK${NC}"
else
    echo -e "  ${YELLOW}SSH key not set up. Setting up now...${NC}"
    # Generate key if needed
    [ ! -f ~/.ssh/id_rsa ] && ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
    echo -e "  ${YELLOW}Enter the GPU machine password when prompted:${NC}"
    ssh-copy-id "$REMOTE"
    echo -e "  ${GREEN}✅ SSH key copied${NC}"
fi

# Check GPU on remote
echo -e "\n  Remote GPU:"
ssh "$REMOTE" "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'nvidia-smi not found'"

# ─── 1. Source code ──────────────────────────────────────────────────────────
echo -e "\n${GREEN}[1/5] Transferring source code...${NC}"
rsync -avz --progress \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='.venv' \
    --exclude='models/' \
    --exclude='__pycache__' \
    --exclude='.git/objects' \
    --exclude='training/task-router' \
    "$LOCAL_DIR/" "$REMOTE:$REMOTE_DIR/"

echo -e "  ${GREEN}✅ Source code transferred${NC}"

# ─── 2. Essential local models ──────────────────────────────────────────────
echo -e "\n${GREEN}[2/5] Transferring essential models (~6GB)...${NC}"
ssh "$REMOTE" "mkdir -p $REMOTE_DIR/models"

# YOLO weights
rsync -avz --progress "$LOCAL_DIR/models/yolo11s.pt" "$REMOTE:$REMOTE_DIR/models/"
rsync -avz --progress "$LOCAL_DIR/models/yolo-pid/" "$REMOTE:$REMOTE_DIR/models/yolo-pid/"

# Task router
rsync -avz --progress "$LOCAL_DIR/models/task-router/" "$REMOTE:$REMOTE_DIR/models/task-router/"

# bge-m3 embeddings
rsync -avz --progress "$LOCAL_DIR/models/bge-m3/" "$REMOTE:$REMOTE_DIR/models/bge-m3/"

# Fine-tuned weights
rsync -avz --progress "$LOCAL_DIR/infra/models/" "$REMOTE:$REMOTE_DIR/infra/models/" 2>/dev/null || true

echo -e "  ${GREEN}✅ Essential models transferred${NC}"

# ─── 3. HuggingFace cache (the big models) ──────────────────────────────────
echo -e "\n${GREEN}[3/5] Transferring HuggingFace model cache...${NC}"
echo -e "  ${YELLOW}This transfers the pre-downloaded LLM weights (~70GB)${NC}"
echo -e "  ${YELLOW}Skip this if the GPU machine has fast internet${NC}"
echo ""
read -p "  Transfer HF cache? (~70GB, saves download time) [Y/n] " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    REMOTE_HF="/home/$GPU_USER/.cache/huggingface/hub"
    ssh "$REMOTE" "mkdir -p $REMOTE_HF"

    # Transfer only the models needed for fine-tuning
    MODELS=(
        "models--Qwen--Qwen2.5-7B-Instruct"
        "models--Qwen--Qwen2.5-VL-7B-Instruct"
        "models--Qwen--Qwen2.5-0.5B-Instruct"
        "models--BAAI--bge-m3"
    )

    for model_dir in "${MODELS[@]}"; do
        src="$HF_CACHE/$model_dir"
        if [ -d "$src" ]; then
            size=$(du -sh "$src" 2>/dev/null | cut -f1)
            echo -e "  Transferring $model_dir ($size)..."
            rsync -a --progress "$src" "$REMOTE:$REMOTE_HF/"
        fi
    done

    # Version file
    scp "$HF_CACHE/version.txt" "$REMOTE:$REMOTE_HF/" 2>/dev/null || true

    echo -e "  ${GREEN}✅ HF cache transferred${NC}"
else
    echo -e "  ${YELLOW}Skipped — models will download from HuggingFace${NC}"
fi

# ─── 4. Training data ───────────────────────────────────────────────────────
echo -e "\n${GREEN}[4/5] Transferring training data...${NC}"
rsync -avz --progress "$LOCAL_DIR/training/yolo-pid/" "$REMOTE:$REMOTE_DIR/training/yolo-pid/"
rsync -avz --progress "$LOCAL_DIR/training/vlm-finetuning/" "$REMOTE:$REMOTE_DIR/training/vlm-finetuning/"
echo -e "  ${GREEN}✅ Training data transferred${NC}"

# ─── 5. Set up remote environment ───────────────────────────────────────────
echo -e "\n${GREEN}[5/5] Setting up Python environment on remote...${NC}"
ssh "$REMOTE" "cd $REMOTE_DIR && bash tools/gpu-session/01_setup_remote.sh" || {
    echo -e "  ${YELLOW}Auto-setup failed. Run manually on the GPU machine:${NC}"
    echo -e "  ${GREEN}cd $REMOTE_DIR && bash tools/gpu-session/01_setup_remote.sh${NC}"
}

# ─── Done ────────────────────────────────────────────────────────────────────
echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ TRANSFER COMPLETE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Now SSH into the GPU machine and run:${NC}"
echo -e "  ${GREEN}ssh $REMOTE${NC}"
echo -e "  ${GREEN}cd $REMOTE_DIR${NC}"
echo -e "  ${GREEN}source .venv/bin/activate${NC}"
echo -e "  ${GREEN}bash tools/gpu-session/02_finetune_all.sh${NC}       # Fine-tune (2-3 hrs)"
echo -e "  ${GREEN}bash tools/gpu-session/03_run_and_screenshot.sh${NC}  # Screenshots (20 min)"
echo ""
echo -e "${YELLOW}To bring results BACK to this PC:${NC}"
echo -e "  ${GREEN}bash tools/gpu-session/06_pull_results.sh $GPU_USER $GPU_IP${NC}"

#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  STEP 2: Set up the remote 24GB GPU machine
#  Run this FIRST on the GPU machine after plugging in the pendrive
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Auto-detect pendrive session directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SESSION_DIR="$(dirname "$SCRIPT_DIR")"
WORK_DIR="$HOME/sovereign-workbench"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SOVEREIGN WORKBENCH — REMOTE GPU SETUP${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "Session dir: $SESSION_DIR"
echo -e "Work dir:    $WORK_DIR"
echo ""

# ─── 1. Check GPU ────────────────────────────────────────────────────────────
echo -e "${GREEN}[1/6] Checking GPU...${NC}"
if command -v nvidia-smi &>/dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1 | tr -d ' ')
    echo -e "  GPU VRAM: ${GPU_MEM}MB"
    if [ "$GPU_MEM" -lt 20000 ]; then
        echo -e "${RED}WARNING: GPU has less than 20GB VRAM. Fine-tuning may OOM.${NC}"
    fi
else
    echo -e "${RED}ERROR: nvidia-smi not found. Is CUDA installed?${NC}"
    exit 1
fi

# ─── 2. Copy code to local disk ─────────────────────────────────────────────
echo -e "\n${GREEN}[2/6] Copying project to local disk...${NC}"
if [ -d "$WORK_DIR" ]; then
    echo -e "  ${YELLOW}$WORK_DIR already exists. Backing up...${NC}"
    mv "$WORK_DIR" "${WORK_DIR}.bak.$(date +%s)"
fi

# Try git clone first (fastest if internet available)
if command -v git &>/dev/null && git ls-remote https://github.com/IFKabir/sovereign-workbench.git HEAD &>/dev/null 2>&1; then
    echo -e "  Cloning from GitHub..."
    git clone https://github.com/IFKabir/sovereign-workbench.git "$WORK_DIR"
else
    echo -e "  No internet — copying from pendrive..."
    cp -r "$SESSION_DIR/sovereign-workbench" "$WORK_DIR"
fi

echo -e "  ${GREEN}✅ Code copied${NC}"

# ─── 3. Copy models ─────────────────────────────────────────────────────────
echo -e "\n${GREEN}[3/6] Copying local models...${NC}"
if [ -d "$SESSION_DIR/models" ]; then
    rsync -av "$SESSION_DIR/models/" "$WORK_DIR/models/"
    echo -e "  ${GREEN}✅ Local models copied${NC}"
else
    echo -e "  ${YELLOW}No local models directory on pendrive${NC}"
fi

# ─── 4. Restore HuggingFace cache ───────────────────────────────────────────
echo -e "\n${GREEN}[4/6] Restoring HuggingFace model cache...${NC}"
HF_CACHE="$HOME/.cache/huggingface/hub"
mkdir -p "$HF_CACHE"

if [ -d "$SESSION_DIR/hf_cache/hub" ]; then
    rsync -av "$SESSION_DIR/hf_cache/hub/" "$HF_CACHE/"
    echo -e "  ${GREEN}✅ HF cache restored ($(du -sh "$HF_CACHE" | cut -f1))${NC}"
else
    echo -e "  ${YELLOW}No HF cache on pendrive — models will download from internet${NC}"
fi

# ─── 5. Set up Python environment ───────────────────────────────────────────
echo -e "\n${GREEN}[5/6] Setting up Python virtual environment...${NC}"
cd "$WORK_DIR"

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip wheel setuptools

# Core ML dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 2>/dev/null \
    || pip install torch torchvision torchaudio

pip install \
    transformers>=4.45.0 \
    accelerate \
    bitsandbytes \
    peft \
    trl \
    datasets \
    ultralytics \
    Pillow \
    httpx \
    fastapi \
    uvicorn \
    python-multipart \
    qdrant-client \
    sentence-transformers \
    onnxruntime \
    psutil \
    pydantic \
    pydantic-settings \
    python-dotenv \
    qwen-vl-utils \
    selenium \
    python-docx \
    PyPDF2 \
    openpyxl

echo -e "  ${GREEN}✅ Python environment ready${NC}"

# ─── 6. Install Node.js for the web UI ───────────────────────────────────────
echo -e "\n${GREEN}[6/6] Setting up Node.js...${NC}"
if command -v node &>/dev/null; then
    echo -e "  Node.js $(node -v) already installed"
else
    echo -e "  Installing Node.js via nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 20
fi

cd "$WORK_DIR/apps/web" && npm install 2>/dev/null || echo "  (npm install deferred)"
cd "$WORK_DIR"

# ─── Done ────────────────────────────────────────────────────────────────────
echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ SETUP COMPLETE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo -e "Python: $(python3 --version)"
echo -e "Torch CUDA: $(python3 -c 'import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A")')"
echo ""
echo -e "${YELLOW}NEXT: Run fine-tuning with:${NC}"
echo -e "  cd $WORK_DIR"
echo -e "  source .venv/bin/activate"
echo -e "  bash tools/gpu-session/02_finetune_all.sh"

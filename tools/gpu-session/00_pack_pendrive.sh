#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  STEP 1: Pack for 32GB pendrive (slim mode)
#  Models download from HuggingFace on the GPU machine
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PENDRIVE="${1:-/media/ifkabir/PENDRIVE}"
DEST="$PENDRIVE/sovereign-gpu-session"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SOVEREIGN WORKBENCH — 32GB PENDRIVE PACKER (SLIM MODE)${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ ! -d "$PENDRIVE" ]; then
    echo -e "${RED}ERROR: Pendrive not found at '$PENDRIVE'${NC}"
    echo -e "${YELLOW}Usage: $0 /path/to/pendrive${NC}"
    exit 1
fi

FREE_GB=$(df --output=avail "$PENDRIVE" | tail -1 | awk '{printf "%.0f", $1/1024/1024}')
echo -e "Pendrive free space: ${GREEN}${FREE_GB}GB${NC}"
echo -e "Estimated need: ${GREEN}~8-10GB${NC} (LLM models download from HuggingFace on GPU machine)"
echo ""

mkdir -p "$DEST"

cd /home/ifkabir/work/sih/sovereign-workbench

# ─── 1. Push to GitHub ──────────────────────────────────────────────────────
echo -e "${GREEN}[1/5] Pushing latest code to GitHub...${NC}"
git add -A 2>/dev/null || true
git commit -m "pre-gpu-session: latest code snapshot $(date +%Y%m%d)" 2>/dev/null || true
git push origin main 2>/dev/null || git push origin master 2>/dev/null || echo "  (push failed — will copy code)"

# ─── 2. Source code (backup, in case no internet) ───────────────────────────
echo -e "\n${GREEN}[2/5] Packing source code (~500MB)...${NC}"
rsync -a --progress \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='.venv' \
    --exclude='models/' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='training/task-router' \
    . "$DEST/sovereign-workbench/"

echo -e "  ${GREEN}✅ Source code packed${NC}"

# ─── 3. Essential models only (no LLMs — those download from HF) ───────────
echo -e "\n${GREEN}[3/5] Packing essential models only (~6GB)...${NC}"
mkdir -p "$DEST/models"

# YOLO weights — needed for P&ID detection
cp -v models/yolo11s.pt "$DEST/models/" 2>/dev/null || true
cp -rv models/yolo-pid/ "$DEST/models/yolo-pid/" 2>/dev/null || true

# Task router — needed for query classification
rsync -a --progress models/task-router/ "$DEST/models/task-router/" 2>/dev/null || true

# bge-m3 — needed for RAG embeddings
rsync -a --progress models/bge-m3/ "$DEST/models/bge-m3/" 2>/dev/null || true

# Fine-tuned YOLO weights if they exist
cp -v infra/models/pid_yolo_best.pt "$DEST/models/" 2>/dev/null || true

echo -e "  ${GREEN}✅ Essential models packed ($(du -sh "$DEST/models/" | cut -f1))${NC}"

# ─── 4. Training data ───────────────────────────────────────────────────────
echo -e "\n${GREEN}[4/5] Packing training data (~50MB)...${NC}"
mkdir -p "$DEST/sovereign-workbench/training"
rsync -a --progress training/yolo-pid/ "$DEST/sovereign-workbench/training/yolo-pid/"
rsync -a --progress training/vlm-finetuning/ "$DEST/sovereign-workbench/training/vlm-finetuning/"
echo -e "  ${GREEN}✅ Training data packed${NC}"

# ─── 5. GPU session scripts ─────────────────────────────────────────────────
echo -e "\n${GREEN}[5/5] Copying GPU session scripts & guide...${NC}"
cp -r tools/gpu-session/ "$DEST/scripts/"
chmod +x "$DEST/scripts/"*.sh 2>/dev/null || true
echo -e "  ${GREEN}✅ Scripts packed${NC}"

# ─── Summary ────────────────────────────────────────────────────────────────
echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ 32GB PENDRIVE PACKED SUCCESSFULLY${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Packed size: $(du -sh "$DEST" | cut -f1)"
echo ""
du -sh "$DEST"/*/ 2>/dev/null
echo ""
echo -e "${YELLOW}⚠️  LLM models (Qwen 7B = 15GB) will download from HuggingFace${NC}"
echo -e "${YELLOW}   on the GPU machine. Make sure it has internet access.${NC}"
echo ""
echo -e "${GREEN}On the GPU machine:${NC}"
echo -e "  1. cd /path/to/pendrive/sovereign-gpu-session"
echo -e "  2. bash scripts/01_setup_remote.sh"
echo -e "  3. bash scripts/02_finetune_all.sh"
echo -e "  4. bash scripts/03_run_and_screenshot.sh"
echo -e "  5. bash scripts/04_pack_results.sh /path/to/pendrive"

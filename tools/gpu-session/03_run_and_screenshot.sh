#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  STEP 4: Run the platform and capture presentation screenshots
#  Captures all capability demos: general Q&A, P&ID, calculations,
#  document reading, and safety compliance
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

SCREENSHOTS_DIR="$WORK_DIR/presentation-screenshots"
mkdir -p "$SCREENSHOTS_DIR"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SOVEREIGN WORKBENCH — SCREENSHOT CAPTURE SUITE${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# ─── Start the platform ─────────────────────────────────────────────────────
echo -e "${GREEN}[1/3] Starting all platform services...${NC}"

# Update vllm_service to use fine-tuned LLM adapter if available
LORA_DIR="$WORK_DIR/infra/models/qwen2.5-7b-industrial-lora"
if [ -d "$LORA_DIR" ] && [ -f "$LORA_DIR/adapter_config.json" ]; then
    echo -e "  ${GREEN}Fine-tuned LLM adapter found — loading with LoRA merge${NC}"
    export USE_LORA_ADAPTER="$LORA_DIR"
fi

# Start services
bash scripts/start_sovereign_ai.sh &
PLATFORM_PID=$!

echo -e "  Waiting for services to be ready..."
sleep 30

# Wait for API to be healthy
for i in $(seq 1 30); do
    if curl -s http://localhost:8080/health | grep -q "healthy" 2>/dev/null; then
        echo -e "  ${GREEN}✅ API is healthy${NC}"
        break
    fi
    sleep 2
done

# Wait for frontend
for i in $(seq 1 20); do
    if curl -s http://localhost:3000 | grep -q "html" 2>/dev/null; then
        echo -e "  ${GREEN}✅ Frontend is ready${NC}"
        break
    fi
    sleep 3
done

# ─── Capture screenshots ────────────────────────────────────────────────────
echo -e "\n${GREEN}[2/3] Capturing presentation screenshots...${NC}"

python3 tools/gpu-session/capture_screenshots.py \
    --output-dir "$SCREENSHOTS_DIR" \
    --base-url "http://localhost:3000" \
    --api-url "http://localhost:8080"

# ─── Cleanup ────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}[3/3] Stopping services...${NC}"
kill $PLATFORM_PID 2>/dev/null || true
pkill -f "apps.vllm_service" 2>/dev/null || true
pkill -f "apps.yolo_service" 2>/dev/null || true
pkill -f "apps.api.main" 2>/dev/null || true

echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ SCREENSHOTS CAPTURED${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Screenshots saved to: $SCREENSHOTS_DIR"
ls -la "$SCREENSHOTS_DIR"/*.png 2>/dev/null | head -20
echo ""
echo -e "${YELLOW}NEXT: Pack results to bring back:${NC}"
echo -e "  bash tools/gpu-session/04_pack_results.sh /path/to/pendrive"

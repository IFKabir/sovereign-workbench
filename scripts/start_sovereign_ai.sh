#!/usr/bin/env bash
# ==============================================================================
# Sovereign AI Workbench (SIH26117) — One-Click Full AI Launcher
# ==============================================================================
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "========================================================================"
echo "  🚀 Starting Sovereign AI Workbench — Full AI Potential Mode"
echo "  MRPL · Air-Gapped Industrial Operations · SIH26117"
echo "========================================================================"
echo -e "${NC}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Ensure virtual environment is active
if [ -d "$REPO_ROOT/.venv" ]; then
    source "$REPO_ROOT/.venv/bin/activate"
fi

# Clean up any existing processes running on target ports
echo -e "${YELLOW}Cleaning up any stale processes on ports 3000, 6333, 8001, 8002, 8080...${NC}"
fuser -k 3000/tcp 8001/tcp 8002/tcp 8080/tcp 2>/dev/null || true
pkill -f "uvicorn apps.vllm_service:app" 2>/dev/null || true
pkill -f "uvicorn apps.yolo_service:app" 2>/dev/null || true
pkill -f "uvicorn apps.api.main:app" 2>/dev/null || true

# Trap process exit to cleanly terminate all background child processes
cleanup() {
    echo -e "\n${RED}Shutting down all Sovereign AI microservices...${NC}"
    fuser -k -9 3000/tcp 8001/tcp 8002/tcp 8080/tcp 2>/dev/null || true
    pkill -9 -f "apps.vllm_service" 2>/dev/null || true
    pkill -9 -f "apps.yolo_service" 2>/dev/null || true
    pkill -9 -f "apps.api.main" 2>/dev/null || true
    kill 0 2>/dev/null || true
}
trap cleanup EXIT SIGINT SIGTERM

# 1. Start / Verify Qdrant Vector DB & Sovereign Sandbox Container Image
echo -e "\n${GREEN}[1/5] Checking Qdrant Vector Database & Docker Sandbox Image...${NC}"
if command -v docker >/dev/null 2>&1; then
    if ! docker ps --format '{{.Names}}' | grep -q "^sovereign-qdrant$"; then
        docker start sovereign-qdrant 2>/dev/null || docker run -d --name sovereign-qdrant -p 6333:6333 qdrant/qdrant:latest 2>/dev/null || true
    fi
    if ! docker image inspect sovereign-sandbox:latest >/dev/null 2>&1; then
        echo -e "${YELLOW}Building sovereign-sandbox:latest Docker container image...${NC}"
        docker build -t sovereign-sandbox:latest -f infra/docker/Dockerfile.sandbox infra/docker
    fi
fi

export VLLM_MODEL_NAME="${VLLM_MODEL_NAME:-models/Qwen2.5-VL-7B-Instruct}"

# 2. Launch Local GPU LLM Engine (Port 8002)
echo -e "\n${GREEN}[2/5] Launching GPU LLM Inference Engine (Qwen2.5-VL-7B on Port 8002)...${NC}"
mkdir -p logs
PORT=8002 VLLM_MODEL_NAME="$VLLM_MODEL_NAME" python -m uvicorn apps.vllm_service:app --host 0.0.0.0 --port 8002 > logs/vllm_service.log 2>&1 &
LLM_PID=$!

# Wait for port 8002 to become active
echo -e "${YELLOW}[*] Awaiting LLM engine readiness on :8002...${NC}"
for i in {1..30}; do
  if curl -s http://localhost:8002/health > /dev/null 2>&1 || curl -s http://localhost:8002/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}[✓] Local LLM engine active on port 8002.${NC}"
    break
  fi
  sleep 1
done

# 3. Launch YOLOv11s Vision Microservice (Port 8001)
echo -e "\n${GREEN}[3/5] Launching YOLOv11s P&ID Detection Service (Port 8001)...${NC}"
python -m uvicorn apps.yolo_service:app --host 0.0.0.0 --port 8001 &
YOLO_PID=$!

sleep 2

# 4. Launch Main API Orchestrator (Port 8080)
echo -e "\n${GREEN}[4/5] Launching FastAPI Agent Orchestrator (Port 8080)...${NC}"
PYTHONPATH=".:packages/shared-schemas:packages/security-audit:packages/agent-core" \
VLLM_BASE_URL=http://localhost:8002/v1 \
VLLM_MODEL_NAME="$VLLM_MODEL_NAME" \
QDRANT_URL=http://localhost:6333 \
YOLO_SERVICE_URL=http://localhost:8001 \
AUDIT_DB_PATH=./data/audit_ledger.db \
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8080 &
API_PID=$!

# 5. Launch Next.js Web UI (Port 3000)
echo -e "\n${GREEN}[5/5] Launching Next.js Industrial Web Dashboard (Port 3000)...${NC}"
if [ -d "$REPO_ROOT/apps/web" ]; then
    cd "$REPO_ROOT/apps/web"
    npm run dev -- --hostname 0.0.0.0 &
    WEB_PID=$!
    cd "$REPO_ROOT"
fi

sleep 4

echo -e "\n${CYAN}========================================================================"
echo -e "  🌟 ALL MICROSERVICES & AGENTIC AI ENGINES RUNNING AT FULL POTENTIAL!"
echo -e "========================================================================"
echo -e "  💻 Web Interface (Industrial UI): ${GREEN}http://localhost:3000${NC}"
echo -e "  ⚙️  API Orchestrator Endpoint:    ${GREEN}http://localhost:8080${NC}"
echo -e "  🧠 GPU LLM Inference Engine:    ${GREEN}http://localhost:8002/v1${NC}"
echo -e "  👁️  YOLOv11s Vision Service:      ${GREEN}http://localhost:8001${NC}"
echo -e "  🗄️  Qdrant Vector Storage:       ${GREEN}http://localhost:6333${NC}"
echo -e "========================================================================"
echo -e "  Press ${RED}Ctrl+C${NC} anytime to stop all background services."
echo -e "========================================================================${NC}\n"

# Wait for background jobs
wait

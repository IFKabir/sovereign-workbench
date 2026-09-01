#!/usr/bin/env bash
# ==============================================================================
# Sovereign AI Workbench (SIH26117) — New PC Automated Setup Script
# ==============================================================================
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "========================================================================"
echo "  Sovereign AI Workbench — Automated System Setup Script"
echo "  SIH26117 · Air-Gapped MRPL Refinery Operations"
echo "========================================================================"
echo -e "${NC}"

# 1. Determine Repository Root Directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
echo -e "${GREEN}[1/7] Repository root verified:${NC} $REPO_ROOT"

# 2. Check System Prerequisites
echo -e "\n${GREEN}[2/7] Checking system dependencies...${NC}"
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python 3 is required but not installed. Exiting.${NC}"; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}Node.js is required but not installed. Exiting.${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}npm is required but not installed. Exiting.${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${YELLOW}Warning: Docker is not installed or not in PATH. Qdrant container check will be skipped.${NC}"; }

# 3. Create & Activate Python Virtual Environment
echo -e "\n${GREEN}[3/7] Setting up Python virtual environment (.venv)...${NC}"
if [ ! -d "$REPO_ROOT/.venv" ]; then
    python3 -m venv "$REPO_ROOT/.venv"
    echo -e "${GREEN}Created virtual environment at $REPO_ROOT/.venv${NC}"
fi

source "$REPO_ROOT/.venv/bin/activate"
pip install --upgrade pip --quiet

# Install core Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
pip install torch transformers ultralytics qdrant-client sentence-transformers fastapi uvicorn onnxruntime pydantic pydantic-settings httpx langgraph requests --quiet

# Install editable packages if pyproject.toml / setup.py exists
for pkg in packages/*; do
    if [ -d "$pkg" ] && ( [ -f "$pkg/pyproject.toml" ] || [ -f "$pkg/setup.py" ] ); then
        echo -e "Installing local package: $pkg"
        pip install -e "$pkg" --quiet || true
    fi
done

# 4. Install Web Frontend Dependencies
echo -e "\n${GREEN}[4/7] Installing Next.js Web Frontend dependencies...${NC}"
if [ -d "$REPO_ROOT/apps/web" ]; then
    cd "$REPO_ROOT/apps/web"
    npm install --quiet
    cd "$REPO_ROOT"
fi

# 5. Start/Verify Qdrant Vector Database Container
echo -e "\n${GREEN}[5/7] Verifying Qdrant Vector Database...${NC}"
if command -v docker >/dev/null 2>&1; then
    if ! docker ps --format '{{.Names}}' | grep -q "^sovereign-qdrant$"; then
        if docker ps -a --format '{{.Names}}' | grep -q "^sovereign-qdrant$"; then
            echo -e "${YELLOW}Starting existing sovereign-qdrant container...${NC}"
            docker start sovereign-qdrant || true
        else
            echo -e "${YELLOW}Spinning up new Qdrant container on port 6333...${NC}"
            docker run -d --name sovereign-qdrant -p 6333:6333 qdrant/qdrant:latest || true
        fi
    else
        echo -e "${GREEN}sovereign-qdrant container is already running on port 6333.${NC}"
    fi
fi

# 6. Seed Vector Database with MRPL Fixture Standards
echo -e "\n${GREEN}[6/7] Seeding Qdrant Vector Database with MRPL standards...${NC}"
PYTHONPATH=".:packages/shared-schemas:packages/security-audit:packages/agent-core" \
python "$REPO_ROOT/scripts/seed_vectordb.py" || true

# 7. Run End-to-End Test Suite Validation
echo -e "\n${GREEN}[7/7] Executing E2E validation test suite...${NC}"
PYTHONPATH=".:packages/shared-schemas:packages/security-audit:packages/agent-core" \
python "$REPO_ROOT/scripts/validate_e2e.py"

echo -e "\n${CYAN}========================================================================"
echo -e "  ✅ SETUP COMPLETE! System is ready for air-gapped execution."
echo -e "  To launch all microservices and agents, run:"
echo -e "  ${GREEN}bash scripts/start_sovereign_ai.sh${NC}"
echo -e "========================================================================${NC}"

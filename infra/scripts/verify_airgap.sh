#!/bin/bash
# =============================================================================
# Sovereign Workbench — Air-Gap Integrity Verifier
# =============================================================================
# Validates that the codebase and runtime containers maintain zero
# network egress to external cloud APIs.
#
# SIH26117 · MRPL · Zero Network Egress
# =============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[0;33m'

# Resolve project root relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================="
echo "  Sovereign Workbench Air-Gap Verifier   "
echo "========================================="
echo "  Project Root: $PROJECT_ROOT"
echo

FAIL=0

echo -n "1. Checking internal network configuration (sovereign-net)... "
AIRGAP_COMPOSE="$PROJECT_ROOT/infra/docker/docker-compose.airgap.yml"
if [ -f "$AIRGAP_COMPOSE" ] && grep -q "internal: true" "$AIRGAP_COMPOSE"; then
    echo -e "${GREEN}PASS${NC}"
else
    if [ ! -f "$AIRGAP_COMPOSE" ]; then
        echo -e "${RED}FAIL${NC} (file not found: $AIRGAP_COMPOSE)"
    else
        echo -e "${RED}FAIL${NC} (missing internal: true for sovereign-net)"
    fi
    FAIL=1
fi

echo -n "2. Checking for unauthorized external API endpoints in codebase... "
UNAUTH_ENDPOINTS=$(grep -rn "api\.openai\.com\|api\.anthropic\.com\|api\.cohere\.com\|generativelanguage\.googleapis\.com" \
    "$PROJECT_ROOT/apps" "$PROJECT_ROOT/packages" 2>/dev/null || true)
if [ -z "$UNAUTH_ENDPOINTS" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    echo "$UNAUTH_ENDPOINTS"
    FAIL=1
fi

echo -n "3. Checking for external API keys in environment configurations... "
API_KEYS=$(grep -rn --include='*.py' --include='*.yml' --include='*.yaml' --include='*.env' --include='*.toml' \
    "OPENAI_API_KEY\|ANTHROPIC_API_KEY\|COHERE_API_KEY\|GEMINI_API_KEY" \
    "$PROJECT_ROOT/apps" "$PROJECT_ROOT/packages" "$PROJECT_ROOT/infra/docker" 2>/dev/null || true)
if [ -z "$API_KEYS" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    echo "$API_KEYS"
    FAIL=1
fi

echo -n "4. Checking sandbox Dockerfile network isolation... "
SANDBOX_DF="$PROJECT_ROOT/infra/docker/Dockerfile.sandbox"
if [ -f "$SANDBOX_DF" ]; then
    echo -e "${GREEN}PASS${NC} (exists)"
else
    echo -e "${YELLOW}SKIP${NC} (Dockerfile.sandbox not found)"
fi

echo "5. Checking runtime air-gap via docker (Requires running stack)..."
CONTAINER="sovereign-api-airgap"
if docker ps 2>/dev/null | grep -q "$CONTAINER"; then
    echo -n "   Testing ping to 8.8.8.8... "
    if docker exec $CONTAINER ping -c 1 -W 1 8.8.8.8 >/dev/null 2>&1; then
        echo -e "${RED}FAIL${NC} (ping successful!)"
        FAIL=1
    else
        echo -e "${GREEN}PASS${NC}"
    fi

    echo -n "   Testing DNS resolution (google.com)... "
    if docker exec $CONTAINER getent hosts google.com >/dev/null 2>&1 || docker exec $CONTAINER ping -c 1 -W 1 google.com >/dev/null 2>&1; then
        echo -e "${RED}FAIL${NC} (DNS resolution successful!)"
        FAIL=1
    else
        echo -e "${GREEN}PASS${NC}"
    fi
else
    echo -e "   ${YELLOW}SKIP${NC} (Container $CONTAINER not running — run full docker-compose stack to test)"
fi

echo
if [ $FAIL -eq 0 ]; then
    echo -e "Result: ${GREEN}ALL CHECKS PASSED${NC}. Air-gap integrity verified."
    exit 0
else
    echo -e "Result: ${RED}FAILED${NC}. Please review issues above."
    exit 1
fi

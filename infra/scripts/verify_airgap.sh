#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[0;33m'

echo "========================================="
echo "  Sovereign Workbench Air-Gap Verifier   "
echo "========================================="
echo

FAIL=0

echo -n "1. Checking internal network configuration (sovereign-net)... "
if grep -q "internal: true" ../docker/docker-compose.airgap.yml; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (missing internal: true for sovereign-net)"
    FAIL=1
fi

echo -n "2. Checking for unauthorized external API endpoints in codebase... "
UNAUTH_ENDPOINTS=$(grep -rn "api\.openai\.com\|api\.anthropic\.com\|api\.cohere\.com\|generativelanguage\.googleapis\.com" ../../apps ../../core 2>/dev/null || true)
if [ -z "$UNAUTH_ENDPOINTS" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    echo "$UNAUTH_ENDPOINTS"
    FAIL=1
fi

echo -n "3. Checking for external API keys in environment configurations... "
API_KEYS=$(grep -rn "OPENAI_API_KEY\|ANTHROPIC_API_KEY\|COHERE_API_KEY\|GEMINI_API_KEY" ../../ 2>/dev/null || true)
if [ -z "$API_KEYS" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    echo "$API_KEYS"
    FAIL=1
fi

echo "4. Checking runtime air-gap via docker (Requires running stack)..."
CONTAINER="sovereign-api-airgap"
if docker ps | grep -q "$CONTAINER"; then
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
    echo -e "${YELLOW}SKIP${NC} (Container $CONTAINER not running)"
fi

echo
if [ $FAIL -eq 0 ]; then
    echo -e "Result: ${GREEN}ALL CHECKS PASSED${NC}. Air-gap integrity verified."
    exit 0
else
    echo -e "Result: ${RED}FAILED${NC}. Air-gap integrity compromised. Please check the logs above."
    exit 1
fi

import sys
import os
from pathlib import Path

# Add project packages to sys.path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "packages" / "shared-schemas"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "security-audit"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "agent-core"))
sys.path.insert(0, str(REPO_ROOT / "apps"))

import pytest
from security_audit.hash_chain import AuditLedger

@pytest.fixture
def temp_ledger(tmp_path):
    db_path = tmp_path / "test_audit.db"
    ledger = AuditLedger(db_path=str(db_path))
    return ledger

import sqlite3
import pytest
from security_audit.hash_chain import AuditLedger

def test_hash_chain_append_and_linkage(temp_ledger: AuditLedger):
    b1 = temp_ledger.append_log(
        user_id="op_01",
        role="OPERATOR",
        query="Check isolation status",
        action="QUERY_STANDARDS",
        models_called=["BGE-M3"],
        token_count=100,
        status="success"
    )
    b2 = temp_ledger.append_log(
        user_id="eng_02",
        role="PROCESS_ENGINEER",
        query="Calculate pipe flow",
        action="RUN_SANDBOX",
        models_called=["CodeSandbox"],
        token_count=150,
        status="success"
    )
    
    assert b1.block_id == 1
    assert b2.block_id == 2
    assert b2.prev_hash == b1.combined_sha256
    isValid, msg = temp_ledger.verify_chain_integrity()
    assert isValid is True

def test_tamper_detection_rederivation(temp_ledger: AuditLedger):
    # Populate blocks
    for i in range(5):
        temp_ledger.append_log(
            user_id=f"user_{i}",
            role="OPERATOR",
            query=f"Query {i}",
            action="READ",
            models_called=["Qwen2.5"],
            token_count=50,
            status="success"
        )
    
    isValid, msg = temp_ledger.verify_chain_integrity()
    assert isValid is True
    
    # Simulate an adversary directly editing row 2 in SQLite
    conn = sqlite3.connect(temp_ledger.db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE audit_logs SET query = 'TAMPERED QUERY' WHERE block_id = 2")
    conn.commit()
    conn.close()
    
    # Verification must fail
    isValid_after, msg_after = temp_ledger.verify_chain_integrity()
    assert isValid_after is False
    assert "tamper" in msg_after.lower() or "broken" in msg_after.lower()

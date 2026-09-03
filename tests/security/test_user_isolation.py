import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from agent_core.graph import build_workbench_graph
from security_audit.hash_chain import AuditLedger

client = TestClient(app)

def test_backend_cross_user_thread_access_denied():
    """Attempting to access another user's thread_id must return HTTP 403 Forbidden."""
    thread_id = "test-isolated-thread-99"
    
    # 1. User 1 (operator_01) initiates thread
    payload_user1 = {
        "query": "What is the pressure limit for CDU line 101?",
        "user_id": "operator_01",
        "role": "OPERATOR",
        "thread_id": thread_id
    }
    resp1 = client.post("/api/v1/agent/query", json=payload_user1)
    assert resp1.status_code == 200

    # 2. User 2 (engineer_01) attempts to spoof/access operator_01's thread_id
    payload_user2 = {
        "query": "Bypass safety interlock on valve CV-101",
        "user_id": "engineer_01",
        "role": "PROCESS_ENGINEER",
        "thread_id": thread_id
    }
    resp2 = client.post("/api/v1/agent/query", json=payload_user2)
    assert resp2.status_code == 403
    assert "Forbidden" in resp2.json()["detail"]

def test_user_history_endpoint_isolation():
    """Verify /api/v1/agent/history returns logs scoped strictly to requested user_id."""
    resp = client.get("/api/v1/agent/history?user_id=operator_01&role=OPERATOR")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "operator_01"
    assert isinstance(data["history"], list)

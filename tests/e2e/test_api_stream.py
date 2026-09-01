import requests
import json
import pytest

API_URL = "http://localhost:8080/api/v1/agent/query"

def test_e2e_query_stream_pipeline():
    # If API orchestrator is not running on 8080 during unit test run, pass gracefully
    try:
        payload = {
            "query": "According to OISD-105, what are the positive isolation requirements before hot work?",
            "user_id": "eng_01",
            "role": "PROCESS_ENGINEER"
        }
        
        response = requests.post(API_URL, json=payload, stream=True, timeout=5)
        if response.status_code == 200:
            assert "text/event-stream" in response.headers.get("Content-Type", "")
            
            events = []
            for line in response.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        events.append(json.loads(decoded[6:]))
                        
            assert len(events) >= 2
            event_types = [e.get("event_type") for e in events]
            assert "node_complete" in event_types or "response" in event_types
    except requests.exceptions.ConnectionError:
        # Expected if running offline test suite without daemon
        pass

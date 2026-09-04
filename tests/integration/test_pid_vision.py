import pytest
from agent_core.nodes.pid_analyzer import analyze_pid, format_pid_inventory
from agent_core.graph import generate_response

@pytest.mark.asyncio
async def test_pid_vision_entity_extraction():
    state = {
        "query": "Verify if the bypass line on Valve CV-101 violates double block and bleed rules"
    }
    result = await analyze_pid(state)
    assert result.get("current_node") == "pid_analyzer"
    assert "pid_results" in result
    assert "pid_summary" in result
    assert "P&ID Schematic Symbol Extraction" in result["pid_summary"]


def test_format_pid_inventory():
    detections = [
        {"label": "centrifugal_pump", "tag": "P-101A", "confidence": 0.99, "bbox_normalized": [0.1, 0.1, 0.2, 0.2]},
        {"label": "centrifugal_pump", "tag": "P-101B", "confidence": 0.98, "bbox_normalized": [0.3, 0.3, 0.2, 0.2]},
        {"label": "instrument_bubble", "tag": "PI-101", "confidence": 0.95, "bbox_normalized": [0.5, 0.5, 0.1, 0.1]},
    ]
    summary = format_pid_inventory(detections)
    assert "Total Entities Detected: 3" in summary
    assert "2 centrifugal_pump(s)" in summary
    assert "1 instrument_bubble(s)" in summary
    assert "P-101A" in summary
    assert "PI-101" in summary


@pytest.mark.asyncio
async def test_generate_response_grounded_on_pid_summary():
    detections = [
        {"label": "centrifugal_pump", "tag": "P-101A", "confidence": 0.99, "bbox_normalized": [0.1, 0.1, 0.2, 0.2]},
        {"label": "instrument_bubble", "tag": "PI-101", "confidence": 0.95, "bbox_normalized": [0.5, 0.5, 0.1, 0.1]},
    ]
    pid_summary = format_pid_inventory(detections)
    state = {
        "query": "How many centrifugal pumps and instrument bubbles were detected in this schematic?",
        "intent": "VISION_SCHEMATIC",
        "pid_results": detections,
        "pid_summary": pid_summary,
    }
    res = await generate_response(state)
    assert "final_response" in res
    assert "P-101A" in res["final_response"] or "centrifugal" in res["final_response"].lower()

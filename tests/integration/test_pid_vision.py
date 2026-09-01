import pytest
from agent_core.nodes.pid_analyzer import analyze_pid

@pytest.mark.asyncio
async def test_pid_vision_entity_extraction():
    state = {
        "query": "Verify if the bypass line on Valve CV-101 violates double block and bleed rules"
    }
    result = await analyze_pid(state)
    assert result.get("current_node") == "analyze_pid"
    assert "pid_results" in result
    res_str = str(result["pid_results"])
    assert "CV-101" in res_str or "valve" in res_str.lower() or "bypass" in res_str.lower()

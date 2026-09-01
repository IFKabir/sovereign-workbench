import pytest
from agent_core.graph import build_workbench_graph
from agent_core.nodes.compliance_auditor import audit_compliance

@pytest.mark.asyncio
async def test_hitl_compliance_audit_flagging():
    # Advisory query -> requires_hitl False
    advisory_state = {
        "query": "What is the flash point of diesel according to MSDS?",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    adv_res = await audit_compliance(advisory_state)
    assert adv_res.get("requires_hitl") is False

    # Safety-critical modification -> requires_hitl True
    critical_state = {
        "query": "Generate a Permit-to-Work (PTW) exception to MODIFY_VALVE_PARAMETER on isolation valve V-101",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    crit_res = await audit_compliance(critical_state)
    assert crit_res.get("requires_hitl") is True
    flags = [f.lower() for f in crit_res.get("compliance_flags", [])]
    assert any(flag in flags for flag in ["permit_to_work", "permit-to-work", "modify_valve_parameter", "ptw", "exception"])

def test_langgraph_compilation():
    graph = build_workbench_graph()
    assert graph is not None

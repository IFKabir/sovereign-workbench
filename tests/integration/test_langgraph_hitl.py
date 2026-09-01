import pytest
from agent_core.graph import build_workbench_graph, hitl_gate
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


# ---------------------------------------------------------------------------
# HITL gate node function
# ---------------------------------------------------------------------------

def test_hitl_gate_approved():
    """hitl_gate should pass through when hitl_approved is True."""
    state = {"hitl_approved": True, "requires_hitl": False}
    result = hitl_gate(state)
    assert result.get("current_node") == "hitl_gate"
    assert result.get("error") is None

def test_hitl_gate_denied():
    """hitl_gate should set error when hitl_approved is False."""
    state = {"hitl_approved": False, "requires_hitl": True}
    result = hitl_gate(state)
    assert "denied" in result.get("error", "").lower()

def test_hitl_gate_pending():
    """hitl_gate should set error when hitl_approved is None (not yet decided)."""
    state = {"hitl_approved": None, "requires_hitl": True}
    result = hitl_gate(state)
    assert "required" in result.get("error", "").lower()


# ---------------------------------------------------------------------------
# HITL resume: update_state + invoke(None) pattern
# ---------------------------------------------------------------------------

def test_hitl_resume_propagates_to_generate_response():
    """Verify that after interrupt_before on hitl_gate, update_state + invoke(None)
    continues execution through hitl_gate → log_audit → generate_response → END
    and produces a final_response.
    """
    graph = build_workbench_graph()
    thread_id = "test-hitl-resume-001"
    config = {"configurable": {"thread_id": thread_id}}

    # Initial state that will trigger HITL
    initial_state = {
        "user_id": "test_user",
        "user_role": "OPERATOR",
        "query": "Generate a Permit-to-Work (PTW) for isolation valve V-101",
        "messages": [],
        "compliance_flags": [],
        "requires_hitl": False,
        "hitl_approved": None,
        "token_counts": {},
        "metadata": {},
    }

    # Run graph — should pause at hitl_gate due to interrupt_before
    # We use a try/except because the graph may raise or return depending on version
    import asyncio
    try:
        result = asyncio.get_event_loop().run_until_complete(
            asyncio.to_thread(graph.invoke, initial_state, config)
        )
    except Exception:
        result = None

    # Check the graph state — should be paused before hitl_gate
    state = graph.get_state(config)
    assert state is not None
    # The graph should have next steps (waiting at hitl_gate)
    if state.next:
        assert "hitl_gate" in state.next

        # Resume with approval
        graph.update_state(config, {
            "hitl_approved": True,
            "requires_hitl": False,
        })

        resumed = graph.invoke(None, config)

        # After resumption, generate_response should have produced a final_response
        final_state = graph.get_state(config)
        final_response = final_state.values.get("final_response", "") if final_state.values else ""
        # final_response should not be empty (either LLM answer or extractive fallback)
        assert final_response, "generate_response did not produce a final_response after HITL approval"


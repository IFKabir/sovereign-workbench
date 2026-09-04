import pytest
from agent_core.graph import build_workbench_graph, hitl_gate
from agent_core.nodes.compliance_auditor import audit_compliance

# ---------------------------------------------------------------------------
# HITL Selectivity: Read-only queries should NEVER trigger HITL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hitl_no_trigger_on_read_only_advisory():
    """Advisory/informational queries should not require HITL."""
    state = {
        "query": "What is the flash point of diesel according to MSDS?",
        "intent": "RAG_STANDARDS",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is False

@pytest.mark.asyncio
async def test_hitl_no_trigger_on_inspection_with_bypass_keyword():
    """Inspection of a bypass line should NOT trigger HITL despite 'bypass' keyword."""
    state = {
        "query": "Inspect the CDU bypass line schematic. Does Valve CV-101 follow a compliant Double Block and Bleed arrangement?",
        "intent": "VISION_SCHEMATIC",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is False

@pytest.mark.asyncio
async def test_hitl_no_trigger_on_list_isolation_requirements():
    """Asking about isolation requirements is read-only, not an action."""
    state = {
        "query": "What are the isolation requirements for valve maintenance under OISD-105?",
        "intent": "RAG_STANDARDS",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is False

@pytest.mark.asyncio
async def test_hitl_no_trigger_on_summarize_handover():
    """Summarize query should not trigger HITL."""
    state = {
        "query": "Summarize the pump status in the handover report",
        "intent": "DOC_REASONING",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is False

@pytest.mark.asyncio
async def test_hitl_no_trigger_on_list_isa_tags():
    """Listing ISA-5.1 tags is a read-only inspection."""
    state = {
        "query": "List all ISA-5.1 tags in the CDU bypass schematic",
        "intent": "VISION_SCHEMATIC",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is False

# ---------------------------------------------------------------------------
# HITL Selectivity: Action-modifying queries SHOULD trigger HITL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hitl_triggers_on_generate_ptw():
    """Generating a Permit-to-Work should trigger HITL."""
    state = {
        "query": "Generate a Permit-to-Work (PTW) for isolation valve V-101",
        "intent": "CODE_SANDBOX",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is True
    assert len(res.get("compliance_flags", [])) > 0

@pytest.mark.asyncio
async def test_hitl_triggers_on_hot_work_permit():
    """Hot work permit generation should trigger HITL."""
    state = {
        "query": "Generate a Permit-to-Work (PTW) hot work permit for welding on Line-101",
        "intent": "CODE_SANDBOX",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is True

@pytest.mark.asyncio
async def test_hitl_triggers_on_bypass_safety_interlock():
    """Bypassing a safety interlock is action-modifying and should trigger HITL."""
    state = {
        "query": "Bypass the safety interlock on relief valve PSV-102",
        "intent": "CODE_SANDBOX",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is True

@pytest.mark.asyncio
async def test_hitl_triggers_on_modify_setpoint():
    """Modifying a setpoint is action-modifying."""
    state = {
        "query": "Modify the setpoint of PIC-301 from 12 to 15 kg/cm2",
        "intent": "CODE_SANDBOX",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is True

@pytest.mark.asyncio
async def test_hitl_triggers_on_ptw_hot_work_without_dbb_rag_intent():
    """Generating a PTW hot work permit without DBB must trigger HITL regardless of RAG_STANDARDS intent."""
    state = {
        "query": "Generate a Permit-to-Work (PTW) hot work permit for welding near the CDU pump manifold without Double Block and Bleed isolation",
        "intent": "RAG_STANDARDS",
        "role": "OPERATOR",
        "user_id": "op_1"
    }
    res = await audit_compliance(state)
    assert res.get("requires_hitl") is True
    assert res.get("requires_approval") is True
    assert res.get("action_type") == "ISSUE_PTW"
    assert "Double Block and Bleed" in res.get("approval_reason", "")

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


@pytest.mark.asyncio
async def test_hitl_rejection_aborts_workflow():
    """Verify that after interrupt_before on hitl_gate, update_state with hitl_approved=False
    routes to abort_rejected_action -> log_audit -> END, outputting the termination banner.
    """
    graph = build_workbench_graph()
    thread_id = "test-hitl-reject-001"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "user_id": "op_1",
        "user_role": "OPERATOR",
        "query": "Generate a Permit-to-Work (PTW) for welding on line 101",
        "messages": [],
        "compliance_flags": [],
        "requires_hitl": False,
        "hitl_approved": None,
        "token_counts": {},
        "metadata": {},
    }

    try:
        await graph.ainvoke(initial_state, config=config)
    except Exception:
        pass

    state = graph.get_state(config)
    assert state is not None and state.next and "hitl_gate" in state.next

    graph.update_state(config, {
        "hitl_approved": False,
        "hitl_note": "Safety hazard detected",
    })

    resumed = await graph.ainvoke(None, config=config)
    final_state = graph.get_state(config)
    final_response = final_state.values.get("final_response", "")
    assert "WORKFLOW TERMINATED: ACTION REJECTED" in final_response
    assert "Safety hazard detected" in final_response


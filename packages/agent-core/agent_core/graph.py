"""LangGraph state-graph orchestrator for the Sovereign AI Workbench.

Defines the deterministic agent workflow:
  Input Classifier → (PID Analyzer ‖ RAG Retriever ‖ Code Sandbox)
  → Compliance Auditor → HITL Gate → Audit Logger → Response Generator → END

Human-in-the-Loop (HITL) approval fires only for safety-critical actions
such as permit-to-work, isolation certificates, or exception generation.
Advisory-only OPERATOR queries pass straight through.

SIH26117 · MRPL · Smart Automation · Zero Network Egress
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_core.state import WorkbenchState
from agent_core.nodes import (
    classify_input, analyze_pid, retrieve_standards,
    execute_code, audit_compliance
)

logger = logging.getLogger(__name__)


def reset_ephemeral_state(state: WorkbenchState) -> dict:
    """Reset ephemeral tool output keys at the start of every new query.
    
    Prevents stale code_output, pid_results, etc. from leaking across
    conversational turns when the LangGraph checkpointer persists state.
    """
    return {
        "code_output": None,
        "sandbox_script": None,
        "sandbox_stdout": None,
        "pid_results": None,
        "retrieved_context": None,
        "rag_results": None,
        "rag_context": None,
        "compliance_flags": [],
        "requires_hitl": False,
        "hitl_approved": None,
        "final_response": None,
        "error": None,
        "current_node": "reset_ephemeral_state",
    }


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def route_after_classification(state: WorkbenchState) -> str:
    """Route to the correct tool node based on classified intent."""
    intent = state.get("intent")
    mapping = {
        "GENERAL_CHAT": "generate_response",
        "VISION_SCHEMATIC": "analyze_pid",
        "RAG_STANDARDS": "retrieve_standards",
        "CODE_SANDBOX": "execute_code",
        "DOC_REASONING": "retrieve_standards",  # uses RAG for doc reasoning
    }
    return mapping.get(intent, "retrieve_standards")


def route_after_audit(state: WorkbenchState) -> str:
    """Decide whether HITL approval is required before proceeding."""
    if state.get("requires_hitl") or state.get("requires_approval"):
        return "hitl_gate"
    return "log_audit"


# ---------------------------------------------------------------------------
# Leaf / utility nodes
# ---------------------------------------------------------------------------

def hitl_gate(state: WorkbenchState) -> dict:
    """Interrupt point for Human-In-The-Loop approval.

    This node only executes after the graph is *resumed* with an explicit
    approval signal.  The ``interrupt_before`` config on this node causes
    LangGraph to pause execution and wait for external input.
    """
    approved = state.get("hitl_approved")
    if approved is False:
        return {
            "error": "HITL approval denied by authorised reviewer.",
            "current_node": "hitl_gate",
        }
    if approved is None:
        return {
            "error": "HITL approval is required but has not been provided.",
            "current_node": "hitl_gate",
        }
    return {"current_node": "hitl_gate"}


def log_audit(state: WorkbenchState) -> dict:
    """Record the interaction in the SHA-256 hash-chained audit ledger.

    Imports AuditLedger lazily so the graph module can be loaded without
    requiring the database to be available at import time.
    """
    try:
        from security_audit.hash_chain import AuditLedger

        db_path = os.environ.get("AUDIT_DB_PATH", "./data/audit_ledger.db")
        ledger = AuditLedger(db_path=db_path)

        models_called: list[str] = []
        token_total: int = 0
        for model_name, count in (state.get("token_counts") or {}).items():
            models_called.append(model_name)
            token_total += count

        ledger.append_log(
            user_id=state.get("user_id", "unknown"),
            role=state.get("user_role", "OPERATOR"),
            query=state.get("query", ""),
            action=state.get("intent", "UNKNOWN"),
            models_called=models_called,
            token_count=token_total or None,
            status="success" if not state.get("error") else "failure",
        )
        logger.info("Audit block appended to ledger")
    except Exception as exc:
        logger.error(f"Audit logging failed: {exc}")

    return {"current_node": "log_audit"}


async def generate_response(state: WorkbenchState) -> dict:
    """Generate the final user-facing response using Qwen2.5-VL via vLLM.

    Aggregates context from preceding nodes and dynamically formats a generic prompt
    payload for the local vLLM endpoint. Falls back to listing raw retrieved grounding chunks
    if LLM inference is offline.
    """
    import httpx

    # Check for GENERAL_CHAT conversational intent
    if state.get("intent") == "GENERAL_CHAT":
        greeting = (
            "Hello! I am the Sovereign AI Workbench assistant deployed at MRPL in an air-gapped environment.\n\n"
            "I am ready to assist you with:\n"
            "• 📐 P&ID Schematic Analysis (YOLOv11s object detection & ISA-5.1 symbol mapping)\n"
            "• 📖 OISD & API Standards Compliance (OISD-118, OISD-105, API-520 RAG retrieval)\n"
            "• ⚡ Engineering Calculations & Python Sandbox Simulations\n"
            "• 🛡️ SHA-256 Hash-Chained Audit Logging & Human-in-the-Loop Approval Gates\n\n"
            "How can I assist your refinery operations today?"
        )
        return {
            "final_response": greeting,
            "current_node": "generate_response",
        }

    vllm_url = os.environ.get("VLLM_BASE_URL", "http://localhost:8002/v1")

    # --- Build generic context block from prior nodes --------------------
    # Only aggregate context from the node that was actually executed
    # in this turn, based on the classified intent.
    context_parts: list[str] = []
    intent = state.get("intent", "")

    # RAG / doc context — always relevant for RAG_STANDARDS, DOC_REASONING, and as supplementary
    retrieved_ctx = state.get("retrieved_context") or state.get("rag_context")
    rag_res = state.get("rag_results")
    if intent in ("RAG_STANDARDS", "DOC_REASONING") or (not intent):
        if retrieved_ctx:
            context_parts.append(f"{retrieved_ctx}")
        elif rag_res and isinstance(rag_res, dict):
            docs = rag_res.get("retrieved_docs") or []
            if docs:
                context_parts.append("\n\n".join(docs))

    # P&ID analysis — only when this turn classified as VISION_SCHEMATIC
    pid_res = state.get("pid_results")
    if intent == "VISION_SCHEMATIC" and pid_res:
        context_parts.append(f"P&ID Analysis Results:\n{pid_res}")

    # Code sandbox output — only when this turn classified as CODE_SANDBOX
    code_out = state.get("code_output")
    if intent == "CODE_SANDBOX" and code_out:
        if isinstance(code_out, dict):
            sandbox_script = state.get("sandbox_script", "")
            stdout = code_out.get("stdout", "")
            stderr = code_out.get("stderr", "")
            exit_code = code_out.get("exit_code", -1)
            parts = []
            if sandbox_script:
                parts.append(f"Generated Python Script:\n```python\n{sandbox_script}\n```")
            if exit_code == 0 and stdout:
                parts.append(f"Execution Output (exit code {exit_code}):\n{stdout}")
            elif exit_code != 0:
                # Feed error context so the LLM can explain the failure
                err_msg = stderr or stdout or "Script execution failed with no output."
                parts.append(f"Script Execution FAILED (exit code {exit_code}):\n{err_msg}")
                parts.append(
                    "Explain the mathematical domain constraint or coding error "
                    "that caused this failure, and provide the corrected calculation."
                )
            context_parts.append("\n\n".join(parts) if parts else f"Code Execution Output:\n{code_out}")
        else:
            context_parts.append(f"Code Execution Output:\n{code_out}")

    if state.get("compliance_flags"):
        context_parts.append(f"Compliance Flags: {', '.join(state['compliance_flags'])}")

    formatted_context_chunks = "\n\n---\n\n".join(context_parts) if context_parts else "No specific document context retrieved."

    system_prompt = "You are an industrial safety AI assistant running on-premise at MRPL."
    user_prompt = (
        f"Answer the user query based strictly on the provided context below. Cite the source document if available.\n\n"
        f"Context:\n{formatted_context_chunks}\n\n"
        f"User Query: {state.get('query', '')}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{vllm_url}/chat/completions",
                json={
                    "model": os.environ.get(
                        "VLLM_MODEL_NAME", "Qwen/Qwen2.5-VL-7B-Instruct"
                    ),
                    "messages": messages,
                    "max_tokens": 2048,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            token_counts = dict(state.get("token_counts") or {})
            model_name = os.environ.get(
                "VLLM_MODEL_NAME", "Qwen/Qwen2.5-VL-7B-Instruct"
            )
            token_counts[model_name] = (
                token_counts.get(model_name, 0) + usage.get("total_tokens", 0)
            )

            return {
                "final_response": answer,
                "token_counts": token_counts,
                "current_node": "generate_response",
            }

    except Exception as exc:
        logger.warning(f"vLLM endpoint unavailable on port 8002 ({exc}), using fallback compliance summary.")
        query_str = state.get("query", "")
        if context_parts:
            fallback = (
                "### Operational Compliance Summary\n\n"
                f"**Query Evaluation**: {query_str}\n\n"
                "#### Grounded Standards Context:\n"
                f"{formatted_context_chunks}\n\n"
                "*(Grounded on local technical standards fixtures. Local reasoning engine in fallback mode.)*"
            )
        else:
            fallback = (
                "### Operational Compliance Summary\n\n"
                f"**Query Evaluation**: {query_str}\n\n"
                "*(Grounded on local technical standards fixtures. Local reasoning engine in fallback mode.)*"
            )
        return {
            "final_response": fallback,
            "error": None,
            "current_node": "generate_response",
        }


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_workbench_graph():
    """Build and compile the LangGraph StateGraph for the sovereign workbench.

    Returns a compiled graph with:
    - MemorySaver checkpointer for state persistence
    - ``interrupt_before`` on the HITL gate node
    """
    builder = StateGraph(WorkbenchState)

    # --- Add nodes -------------------------------------------------------
    builder.add_node("classify_input", classify_input)
    builder.add_node("reset_ephemeral_state", reset_ephemeral_state)
    builder.add_node("analyze_pid", analyze_pid)
    builder.add_node("retrieve_standards", retrieve_standards)
    builder.add_node("execute_code", execute_code)
    builder.add_node("audit_compliance", audit_compliance)
    builder.add_node("hitl_gate", hitl_gate)
    builder.add_node("log_audit", log_audit)
    builder.add_node("generate_response", generate_response)

    # --- Entry point -----------------------------------------------------
    builder.set_entry_point("reset_ephemeral_state")
    builder.add_edge("reset_ephemeral_state", "classify_input")

    # --- Conditional routing after classification ------------------------
    builder.add_conditional_edges(
        "classify_input",
        route_after_classification,
    )

    # --- All tool nodes converge to compliance audit ---------------------
    builder.add_edge("analyze_pid", "audit_compliance")
    builder.add_edge("retrieve_standards", "audit_compliance")
    builder.add_edge("execute_code", "audit_compliance")

    # --- Conditional HITL gate -------------------------------------------
    builder.add_conditional_edges(
        "audit_compliance",
        route_after_audit,
    )

    # --- Linear tail -----------------------------------------------------
    builder.add_edge("hitl_gate", "log_audit")
    builder.add_edge("log_audit", "generate_response")
    builder.add_edge("generate_response", END)

    # --- Compile with checkpointer & HITL interrupt ----------------------
    memory = MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["hitl_gate"],
    )


# ---------------------------------------------------------------------------
# SSE streaming helper
# ---------------------------------------------------------------------------

async def stream_graph_events(
    graph: Any,
    state: dict,
    config: dict,
) -> AsyncGenerator[dict, None]:
    """Yield ``StreamEvent`` dicts suitable for Server-Sent Events.

    Each event includes the node name, event type, data payload,
    timestamp, and (where available) token counts.
    """
    async for event in graph.astream_events(state, config=config, version="v2"):
        node_name = event.get("name")
        yield {
            "event_type": event.get("event", "on_chain_stream"),
            "node_name": node_name,
            "data": event.get("data", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tokens_generated": None,
        }


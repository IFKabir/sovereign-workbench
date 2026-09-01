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
    if state.get("requires_hitl"):
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

    Aggregates context from preceding nodes (P&ID analysis, RAG results,
    code output) and calls the local vLLM endpoint to synthesise a
    coherent, grounded answer.
    """
    import httpx

    vllm_url = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")

    # --- Build context from prior nodes ---------------------------------
    context_parts: list[str] = []

    if state.get("pid_results"):
        context_parts.append(
            f"P&ID Analysis Results:\n{state['pid_results']}"
        )
    if state.get("rag_results"):
        context_parts.append(
            f"Standards / Document Retrieval:\n{state['rag_results']}"
        )
    if state.get("code_output"):
        co = state["code_output"]
        context_parts.append(
            f"Code Execution Output (exit {co.get('exit_code', '?')}):\n"
            f"stdout: {co.get('stdout', '')}\n"
            f"stderr: {co.get('stderr', '')}"
        )

    if state.get("compliance_flags"):
        context_parts.append(
            f"Compliance Flags: {', '.join(state['compliance_flags'])}"
        )

    context_block = "\n\n---\n\n".join(context_parts) if context_parts else ""

    system_prompt = (
        "You are the Sovereign AI Workbench assistant deployed at MRPL. "
        "You operate in a fully air-gapped environment. Provide concise, "
        "technically accurate responses grounded in the context provided. "
        "Always cite the relevant standard or data source."
    )

    messages = [
        {"role": "system", "content": system_prompt},
    ]
    if context_block:
        messages.append({"role": "assistant", "content": f"[Context]\n{context_block}"})
    messages.append({"role": "user", "content": state.get("query", "")})

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
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
        logger.error(f"Response generation failed: {exc}")
        # Provide a graceful fallback using whatever context we have
        fallback = (
            "I was unable to generate a full response due to a model "
            "connectivity issue. Here is the raw context gathered:\n\n"
            + (context_block or "No context was gathered.")
        )
        return {
            "final_response": fallback,
            "error": str(exc),
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
    builder.add_node("analyze_pid", analyze_pid)
    builder.add_node("retrieve_standards", retrieve_standards)
    builder.add_node("execute_code", execute_code)
    builder.add_node("audit_compliance", audit_compliance)
    builder.add_node("hitl_gate", hitl_gate)
    builder.add_node("log_audit", log_audit)
    builder.add_node("generate_response", generate_response)

    # --- Entry point -----------------------------------------------------
    builder.set_entry_point("classify_input")

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


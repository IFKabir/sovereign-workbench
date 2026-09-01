from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import uuid
import asyncio
from datetime import datetime, timezone

from agent_core.graph import build_workbench_graph

router = APIRouter()

# Graph instance with checkpointer
graph_app = build_workbench_graph()

class AgentQueryRequest(BaseModel):
    query: str
    user_id: str = "user-01"
    role: str = "OPERATOR"
    thread_id: Optional[str] = None
    attachments: Optional[List[str]] = None

class HITLApprovalResponse(BaseModel):
    thread_id: str
    approved: bool
    feedback: Optional[str] = None
    role: str = "SAFETY_OFFICER"

from shared_schemas.rbac import RBACRole

# Role-based access control dependency
async def rbac_guard(role: str = "OPERATOR") -> str:
    """Ensure user has required permissions to interact with agents."""
    valid_roles = [r.name for r in RBACRole]
    if not role or role.upper() not in valid_roles:
        raise HTTPException(status_code=403, detail="Invalid role or insufficient permissions")
    return role.upper()

@router.post("/query")
async def agent_query(request: AgentQueryRequest):
    """
    Main agent query endpoint.
    Executes the workbench LangGraph and streams state events / final response via SSE.
    """
    await rbac_guard(request.role)
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "user_id": request.user_id,
        "user_role": request.role,
        "query": request.query,
        "messages": [],
        "compliance_flags": [],
        "requires_hitl": False,
        "hitl_approved": None,
        "token_counts": {},
        "metadata": {}
    }

    async def event_stream():
        try:
            # Yield initial thread event
            yield f'data: {json.dumps({"event_type": "init", "thread_id": thread_id})}\n\n'
            
            # Stream graph execution steps
            async for output in graph_app.astream(initial_state, config=config):
                for node_name, node_state in output.items():
                    # Check if HITL interrupt triggered
                    if node_name == "audit_compliance" and node_state.get("requires_hitl"):
                        flags = node_state.get("compliance_flags", ["CRITICAL_ACTION"])
                        hitl_payload = {
                            "event_type": "hitl_required",
                            "status": "WAITING_APPROVAL",
                            "requires_approval": True,
                            "thread_id": thread_id,
                            "data": {
                                "action_type": flags[0].upper() if flags else "MODIFY_VALVE_PARAMETER",
                                "risk_level": "HIGH",
                                "draft_content": f"Safety-critical action requested: '{request.query}'. Requires supervisor authorization.",
                                "compliance_flags": [f"Flagged requirement: {f.replace('_', ' ').title()}" for f in flags],
                                "required_role": "SAFETY_OFFICER"
                            }
                        }
                        yield f'data: {json.dumps(hitl_payload)}\n\n'
                        yield 'data: {"event_type": "done"}\n\n'
                        return
                    
                    # Yield normal node output
                    event_data = {
                        "event_type": "node_complete",
                        "node_name": node_name,
                        "status": "COMPLETED",
                        "requires_approval": False,
                        "data": {
                            "intent": node_state.get("intent"),
                            "final_response": node_state.get("final_response")
                        }
                    }
                    yield f'data: {json.dumps(event_data)}\n\n'
            
            # Check final graph state for output or interrupted state
            current_state = graph_app.get_state(config)
            if current_state and current_state.next and "hitl_gate" in current_state.next:
                state_values = current_state.values
                flags = state_values.get("compliance_flags", ["SAFETY_CRITICAL_ACTION"])
                hitl_payload = {
                    "event_type": "hitl_required",
                    "status": "WAITING_APPROVAL",
                    "requires_approval": True,
                    "thread_id": thread_id,
                    "data": {
                        "action_type": flags[0].upper() if flags else "SAFETY_MODIFICATION",
                        "risk_level": "HIGH",
                        "draft_content": f"Requested action requires authorization: {request.query}",
                        "compliance_flags": [f"Safety requirement: {f.replace('_', ' ').title()}" for f in flags],
                        "required_role": "SAFETY_OFFICER"
                    }
                }
                yield f'data: {json.dumps(hitl_payload)}\n\n'
            else:
                final_res = current_state.values.get("final_response") if (current_state and current_state.values) else None
                if not final_res:
                    final_res = "Query processed successfully."
                yield f'data: {json.dumps({"event_type": "response", "status": "COMPLETED", "requires_approval": False, "data": {"content": final_res}})}\n\n'
                
        except Exception as e:
            yield f'data: {json.dumps({"event_type": "error", "error": str(e)})}\n\n'
            
        yield 'data: {"event_type": "done"}\n\n'

    return StreamingResponse(event_stream(), media_type='text/event-stream')

@router.post("/hitl/approve")
async def hitl_approve(response: HITLApprovalResponse):
    """
    Human-In-The-Loop approval endpoint.
    Resumes an interrupted graph execution with approval status.
    """
    config = {"configurable": {"thread_id": response.thread_id}}
    
    # Check if thread is waiting for approval
    state = graph_app.get_state(config)
    if not state or not state.next:
        return {
            "status": "success",
            "thread_id": response.thread_id,
            "approved": response.approved,
            "message": f"Approval signal recorded for thread {response.thread_id}."
        }
        
    # Resume graph execution
    update_state = {
        "hitl_approved": response.approved,
        "requires_hitl": False
    }
    
    result = graph_app.invoke(update_state, config=config)
    
    return {
        "status": "success",
        "thread_id": response.thread_id,
        "approved": response.approved,
        "final_response": result.get("final_response", "Action processed after HITL review.")
    }

@router.get("/trace/{task_id}")
async def get_trace(task_id: str) -> Dict[str, Any]:
    """Retrieve full execution trace for a given task ID."""
    return {
        "task_id": task_id,
        "trace": [
            {"step": 1, "action": "classify_input", "status": "success"},
            {"step": 2, "action": "audit_compliance", "status": "success"}
        ]
    }

@router.get("/tasks")
async def list_tasks() -> List[Dict[str, Any]]:
    """List recent tasks executed by the agent."""
    return [
        {"task_id": "t-1001", "status": "completed", "timestamp": datetime.now(timezone.utc).isoformat()}
    ]

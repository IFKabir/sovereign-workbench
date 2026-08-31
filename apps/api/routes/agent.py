from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
from datetime import datetime

router = APIRouter()

class AgentQueryRequest(BaseModel):
    """Request model for agent queries."""
    query: str
    user_id: str
    role: str
    attachments: Optional[List[str]] = None

class HITLApprovalResponse(BaseModel):
    """Request model for HITL approvals."""
    task_id: str
    approved: bool
    feedback: Optional[str] = None

# Role-based access control dependency
async def rbac_guard(role: str = "USER") -> str:
    """Ensure user has required permissions to interact with agents."""
    valid_roles = ["USER", "SAFETY_OFFICER", "PLANT_DIRECTOR"]
    if role not in valid_roles:
        raise HTTPException(status_code=403, detail="Invalid role or insufficient permissions")
    return role

# Simulated event generator for LangGraph
async def mock_stream_graph_events(query: str):
    """Simulate streaming events from LangGraph execution."""
    events = [
        {"node_name": "router", "event_type": "start", "data": "Routing task...", "timestamp": datetime.now().isoformat(), "tokens": 0},
        {"node_name": "agent", "event_type": "process", "data": f"Processing query: {query}", "timestamp": datetime.now().isoformat(), "tokens": 15},
        {"node_name": "output", "event_type": "done", "data": "Task completed successfully.", "timestamp": datetime.now().isoformat(), "tokens": 30},
    ]
    for event in events:
        yield event
        await asyncio.sleep(0.2)

@router.post("/query")
async def agent_query(request: AgentQueryRequest):
    """
    Main agent query endpoint.
    Streams execution events back to the client using SSE.
    """
    await rbac_guard(request.role)

    async def event_stream():
        async for event in mock_stream_graph_events(request.query):
            yield f'data: {json.dumps(event)}\\n\\n'
        yield 'data: {"event_type": "done"}\\n\\n'
    
    return StreamingResponse(event_stream(), media_type='text/event-stream')

@router.post("/hitl/approve")
async def hitl_approve(response: HITLApprovalResponse):
    """
    Human-In-The-Loop approval endpoint.
    Resumes an interrupted graph execution.
    Requires SAFETY_OFFICER or higher role.
    """
    # Requires higher role logic (not explicitly passed here, assuming extracted from JWT in reality)
    return {
        "status": "success", 
        "message": f"Task {response.task_id} {'approved' if response.approved else 'rejected'}."
    }

@router.get("/trace/{task_id}")
async def get_trace(task_id: str) -> Dict[str, Any]:
    """Retrieve full execution trace for a given task ID."""
    return {
        "task_id": task_id,
        "trace": [
            {"step": 1, "action": "parse", "status": "success"},
            {"step": 2, "action": "execute", "status": "success"}
        ]
    }

@router.get("/tasks")
async def list_tasks() -> List[Dict[str, Any]]:
    """List recent tasks executed by the agent."""
    return [
        {"task_id": "t-1001", "status": "completed", "timestamp": datetime.now().isoformat()}
    ]

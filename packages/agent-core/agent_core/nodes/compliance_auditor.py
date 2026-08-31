import os
import httpx
from agent_core.state import WorkbenchState
import logging

logger = logging.getLogger(__name__)

ACTION_TYPES = [
    'permit_to_work', 'isolation_certificate', 'exception_generation', 
    'safety_override', 'hot_work_permit', 'confined_space_entry', 
    'pressure_test_authorization'
]

async def audit_compliance(state: WorkbenchState) -> dict:
    """Reviews draft outputs for safety-critical patterns to trigger HITL."""
    query = state.get("query", "").lower()
    role = state.get("user_role", "OPERATOR")
    
    # Analyze query and possible draft responses
    detected_flags = state.get("compliance_flags", [])
    
    # Simple keyword check; more advanced implementations would use Qwen2.5-VL to check compliance classification
    for action in ACTION_TYPES:
        if action.replace("_", " ") in query:
            if action not in detected_flags:
                detected_flags.append(action)
                
    requires_hitl = False
    
    if detected_flags:
        # If OPERATOR purely asks for advisory information (e.g. "what is hot work?"), it might not trigger HITL. 
        # But for strict safety, we flag it if actionable keywords are present and role is restrictive.
        requires_hitl = True

    return {
        "compliance_flags": detected_flags,
        "requires_hitl": requires_hitl,
        "current_node": "audit_compliance"
    }

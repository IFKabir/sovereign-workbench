import logging
from agent_core.state import WorkbenchState

logger = logging.getLogger(__name__)

CRITICAL_SAFETY_ACTIONS = [
    'permit_to_work', 'permit-to-work', 'issue_ptw', 'isolation_certificate', 'exception_generation', 
    'safety_override', 'hot_work_permit', 'confined_space_entry', 
    'pressure_test_authorization', 'modify_valve_parameter', 'bypass_safety_interlock',
    'bypassing', 'isolation_valve', 'exception'
]

async def audit_compliance(state: WorkbenchState) -> dict:
    """Reviews draft outputs for safety-critical patterns to trigger HITL approval.
    
    requires_hitl defaults to False. It only evaluates to True when an explicit
    safety-critical modification (e.g., MODIFY_VALVE_PARAMETER, ISSUE_PTW, BYPASS_SAFETY_INTERLOCK)
    is present in the drafted plan/query.
    """
    query = state.get("query", "").lower()
    query_normalized = query.replace("-", " ").replace("_", " ")
    intent = state.get("intent", "")
    
    detected_flags = list(state.get("compliance_flags") or [])
    
    # Conversational queries never trigger HITL
    if intent == "GENERAL_CHAT":
        return {
            "compliance_flags": [],
            "requires_hitl": False,
            "current_node": "audit_compliance"
        }
    
    # Check for explicit safety-critical modification keywords
    for action in CRITICAL_SAFETY_ACTIONS:
        action_clean = action.replace("-", " ").replace("_", " ")
        if action_clean in query_normalized or action in query:
            if action not in detected_flags:
                detected_flags.append(action)
    
    # HITL is required ONLY if explicit safety-critical actions are detected
    requires_hitl = len(detected_flags) > 0
    
    return {
        "compliance_flags": detected_flags,
        "requires_hitl": requires_hitl,
        "current_node": "audit_compliance"
    }

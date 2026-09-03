import logging
from typing import Dict, Any
from agent_core.state import WorkbenchState

logger = logging.getLogger(__name__)

# High-risk action patterns that MUST trigger HITL pause regardless of classified intent
CRITICAL_ACTION_PATTERNS = [
    "generate a permit-to-work",
    "generate permit-to-work",
    "generate a permit",
    "generate permit",
    "generate a ptw",
    "generate ptw",
    "issue ptw",
    "issue permit",
    "create permit",
    "create a ptw",
    "hot work permit",
    "permit-to-work",
    "bypass relief valve",
    "bypass valve",
    "bypass safety",
    "bypass the safety",
    "bypass safety interlock",
    "bypass the interlock",
    "override interlock",
    "override the interlock",
    "modify setpoint",
    "modify the setpoint",
    "isolate line",
    "isolate the line",
    "disable alarm",
    "disable the alarm",
    "issue certificate",
    "execute change"
]

# Explicit high-risk safety deviations
HAZARD_OVERRIDE_PATTERNS = [
    "without double block and bleed",
    "without dbb",
    "no dbb",
    "without isolation",
    "without positive isolation",
    "bypass dbb"
]

async def audit_compliance(state: WorkbenchState) -> Dict[str, Any]:
    """Reviews draft outputs and queries for safety-critical patterns to trigger HITL approval.

    CRITICAL_ACTION_PATTERNS and HAZARD_OVERRIDE_PATTERNS ALWAYS take precedence
    over route classification (including RAG_STANDARDS, DOC_REASONING, etc.).
    """
    query = (state.get("query") or "").lower().strip()

    # 1. First: Check for critical action patterns or hazardous isolation deviations
    is_critical_action = any(pattern in query for pattern in CRITICAL_ACTION_PATTERNS)
    is_hazardous_deviation = any(pattern in query for pattern in HAZARD_OVERRIDE_PATTERNS)

    # If the user is actively asking to generate/issue a permit, bypass an interlock,
    # or perform work with missing safety isolation, HITL MUST TRIGGER:
    if is_critical_action or is_hazardous_deviation or state.get("action_type") in ["ISSUE_PTW", "BYPASS_SAFETY_INTERLOCK"]:
        # Exclude purely informational queries (e.g., "what is a ptw", "what are the isolation requirements")
        informational_prefixes = ["what is", "what are", "according to", "explain", "summarize", "list"]
        is_informational = any(query.startswith(p) for p in informational_prefixes) and not is_critical_action

        if not is_informational:
            approval_reason = (
                "Safety-Critical Permit Generation Requested: Hot work requested without standard "
                "Double Block and Bleed (DBB) positive isolation. Mandatory review required."
                if is_hazardous_deviation
                else f"Safety-Critical Action Requested: '{query}'. Mandatory review required."
            )
            action_type = (
                "ISSUE_PTW" if ("permit" in query or "ptw" in query) else "BYPASS_SAFETY_INTERLOCK"
            )
            flag = "CRITICAL_ACTION_GENERATION" if is_critical_action else "HAZARD_ISOLATION_DEVIATION"

            logger.info(f"HITL triggered for query: '{query[:80]}...' — flag: {flag}")

            return {
                "requires_approval": True,
                "requires_hitl": True,
                "status": "WAITING_APPROVAL",
                "risk_level": "HIGH",
                "action_type": action_type,
                "approval_reason": approval_reason,
                "compliance_flags": [flag],
                "current_node": "audit_compliance",
            }

    # 2. Purely read-only intent fallback
    logger.debug(f"No HITL required for query: '{query[:80]}...'")
    return {
        "requires_approval": False,
        "requires_hitl": False,
        "status": "APPROVED",
        "risk_level": "LOW",
        "compliance_flags": [],
        "current_node": "audit_compliance",
    }

# Function alias for compliance_auditor
compliance_auditor = audit_compliance

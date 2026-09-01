import logging
import re
from agent_core.state import WorkbenchState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Read-only intents and keywords that NEVER trigger HITL
# ---------------------------------------------------------------------------

READ_ONLY_INTENTS = {"RAG_STANDARDS", "DOC_REASONING", "GENERAL_CHAT"}

READ_ONLY_KEYWORDS = [
    "what is", "what are", "according to", "list", "inspect", "check",
    "summarize", "explain", "identify", "describe", "show", "find",
    "retrieve", "lookup", "tell me", "does", "is the", "how to",
    "review", "compare", "verify",
]

# ---------------------------------------------------------------------------
# Action-modifying patterns that DO require HITL approval
# These are multi-word phrases to avoid false-positive matching
# ---------------------------------------------------------------------------

ACTION_MODIFYING_PATTERNS = [
    r"generate\s+(?:a\s+)?permit",
    r"issue\s+(?:a\s+)?(?:ptw|permit)",
    r"create\s+(?:a\s+)?(?:ptw|permit)",
    r"bypass\s+(?:the\s+)?(?:relief\s+valve|safety\s+interlock|interlock)",
    r"override\s+(?:the\s+)?interlock",
    r"modify\s+(?:the\s+)?(?:setpoint|valve\s+parameter|parameter)",
    r"isolate\s+(?:the\s+)?line",
    r"disable\s+(?:the\s+)?alarm",
    r"issue\s+(?:an?\s+)?(?:isolation\s+)?certificate",
    r"execute\s+(?:a\s+)?change",
    r"hot\s+work\s+permit",
    r"confined\s+space\s+entry",
    r"pressure\s+test\s+authorization",
    r"modify_valve_parameter",
    r"bypass_safety_interlock",
    r"ptw\s+(?:exception|for)",
    r"permit[- ]to[- ]work",
]

_ACTION_REGEXES = [re.compile(p, re.IGNORECASE) for p in ACTION_MODIFYING_PATTERNS]


async def audit_compliance(state: WorkbenchState) -> dict:
    """Reviews draft outputs for safety-critical patterns to trigger HITL approval.

    HITL is triggered ONLY for explicit state-modifying actions (permit
    generation, interlock overrides, valve parameter modifications, etc.).
    Read-only queries (inspection, retrieval, summarization) NEVER trigger
    HITL, regardless of the safety-related vocabulary they contain.
    """
    query = state.get("query", "")
    query_lower = query.lower()
    intent = state.get("intent", "")

    detected_flags: list[str] = []

    # ── Fast path: read-only intents never trigger HITL ──────────────────
    if intent in READ_ONLY_INTENTS:
        return {
            "compliance_flags": [],
            "requires_hitl": False,
            "current_node": "audit_compliance",
        }

    # ── Fast path: if query is clearly read-only by keyword, skip HITL ──
    if any(kw in query_lower for kw in READ_ONLY_KEYWORDS):
        # But still check if it also matches an action pattern
        has_action = any(rx.search(query_lower) for rx in _ACTION_REGEXES)
        if not has_action:
            return {
                "compliance_flags": [],
                "requires_hitl": False,
                "current_node": "audit_compliance",
            }

    # ── Check for explicit action-modifying patterns ────────────────────
    for i, rx in enumerate(_ACTION_REGEXES):
        if rx.search(query_lower):
            flag = ACTION_MODIFYING_PATTERNS[i].replace(r"\s+", "_").replace(r"(?:a\\s+)?", "").replace(r"(?:the\\s+)?", "")
            # Use a cleaner flag name
            match = rx.search(query_lower)
            if match:
                flag = match.group(0).strip().replace(" ", "_")
                if flag not in detected_flags:
                    detected_flags.append(flag)

    requires_hitl = len(detected_flags) > 0

    if requires_hitl:
        logger.info(f"HITL triggered for query: '{query[:80]}...' — flags: {detected_flags}")
    else:
        logger.debug(f"No HITL required for query: '{query[:80]}...'")

    return {
        "compliance_flags": detected_flags,
        "requires_hitl": requires_hitl,
        "current_node": "audit_compliance",
    }

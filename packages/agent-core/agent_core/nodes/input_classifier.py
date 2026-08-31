import logging
from agent_core.state import WorkbenchState
from agent_core.router import TaskRouter

logger = logging.getLogger(__name__)
router = TaskRouter()

def classify_input(state: WorkbenchState) -> dict:
    """Classifies user input to determine task intent."""
    query = state.get("query", "")
    intent = router.classify(query)
    
    logger.info(f"Classified query with intent: {intent}")
    
    return {
        "intent": intent,
        "current_node": "classify_input"
    }

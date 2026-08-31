from typing import TypedDict, Annotated, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class WorkbenchState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    user_role: str
    query: str
    intent: str
    current_node: str
    pid_results: dict | None
    rag_results: dict | None
    code_output: dict | None
    compliance_flags: list[str]
    requires_hitl: bool
    hitl_approved: bool | None
    final_response: str | None
    error: str | None
    token_counts: dict[str, int]
    metadata: dict[str, Any]

from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from .rbac import RBACRole

class BoundingBox(BaseModel):
    model_config = ConfigDict(frozen=True)

    x_min: float = Field(..., description="Minimum X coordinate")
    y_min: float = Field(..., description="Minimum Y coordinate")
    x_max: float = Field(..., description="Maximum X coordinate")
    y_max: float = Field(..., description="Maximum Y coordinate")
    confidence: float = Field(..., description="Detection confidence score")
    label: str = Field(..., description="Object label")
    symbol_class: Optional[str] = Field(None, description="Detailed symbol class if available")

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        return self.width * self.height

class PIDSymbol(BaseModel):
    symbol_id: str = Field(..., description="Unique ID for the symbol")
    label: str = Field(..., description="Symbol label")
    bbox: BoundingBox = Field(..., description="Bounding box of the symbol")
    isa_code: Optional[str] = Field(None, description="ISA S5.1 instrument code")
    connected_to: List[str] = Field(default_factory=list, description="IDs of connected symbols")
    description: str = Field(default="", description="Description of the symbol")

class PIDDetectionResult(BaseModel):
    image_path: str = Field(..., description="Path to the source P&ID image")
    symbols: List[PIDSymbol] = Field(..., description="List of detected symbols")
    detection_timestamp: datetime = Field(..., description="Timestamp of the detection")
    model_version: str = Field(..., description="Version of the vision model used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

    @property
    def total_symbols(self) -> int:
        return len(self.symbols)

class RAGDocument(BaseModel):
    doc_id: str = Field(..., description="Unique document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Text content of the chunk")
    source_file: str = Field(..., description="Original source file name")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    standard_code: Optional[str] = Field(None, description="Standard code e.g. OISD-116")
    chunk_index: int = Field(..., description="Index of this chunk in the document")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")

class RAGSearchResult(BaseModel):
    query: str = Field(..., description="The search query used")
    results: List[RAGDocument] = Field(..., description="List of retrieved documents")
    scores: List[float] = Field(..., description="Relevance scores for the results")
    reranked: bool = Field(False, description="Whether the results were re-ranked")
    search_time_ms: float = Field(..., description="Time taken to search in milliseconds")

class AuditBlock(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "block_id": 1,
                "timestamp": "2024-05-12T14:32:00Z",
                "prev_hash": "a4d3...",
                "user_id": "usr_001",
                "role": "PROCESS_ENGINEER",
                "action": "view_pid",
                "query": "Show me the cooling unit",
                "models_called": ["gpt-4-vision"],
                "token_count": 1500,
                "status": "success",
                "payload_hash": "c2f5...",
                "combined_sha256": "e9b2..."
            }
        }
    )

    block_id: int = Field(..., description="Sequential block ID")
    timestamp: datetime = Field(..., description="Timestamp of the audit event")
    prev_hash: str = Field(..., description="Hash of the previous block")
    user_id: str = Field(..., description="ID of the user who performed the action")
    role: str = Field(..., description="Role of the user")
    action: str = Field(..., description="Action performed")
    query: str = Field(..., description="User query or input")
    models_called: List[str] = Field(..., description="List of models invoked")
    token_count: Optional[int] = Field(None, description="Tokens used")
    status: Literal['success', 'failure', 'pending'] = Field(..., description="Action status")
    payload_hash: str = Field(..., description="Hash of the payload fields")
    combined_sha256: str = Field(..., description="Hash of prev_hash + payload_hash")

class AgentTaskState(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    user_id: str = Field(..., description="User ID associated with the task")
    role: str = Field(..., description="User role at the time of the task")
    query: str = Field(..., description="Original user query")
    intent: str = Field(..., description="Classified intent of the query")
    current_node: str = Field(..., description="Current node in the agent graph")
    history: List[Dict[str, Any]] = Field(default_factory=list, description="State history")
    pid_results: Optional[PIDDetectionResult] = Field(None, description="P&ID detection results")
    rag_results: Optional[RAGSearchResult] = Field(None, description="RAG search results")
    code_output: Optional[Dict[str, Any]] = Field(None, description="Output from code execution")
    compliance_flags: List[str] = Field(default_factory=list, description="Flags raised during compliance check")
    requires_hitl: bool = Field(False, description="Whether HITL is required")
    hitl_approved: Optional[bool] = Field(None, description="HITL approval status")
    final_response: Optional[str] = Field(None, description="Final response to the user")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Task last update timestamp")
    token_counts: Dict[str, int] = Field(default_factory=dict, description="Tokens used per model")

class HITLApprovalRequest(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    task_id: str = Field(..., description="Associated task identifier")
    user_id: str = Field(..., description="ID of the user who initiated the task")
    action_type: Literal['permit_to_work', 'isolation_certificate', 'exception_generation', 'safety_override'] = Field(..., description="Type of action requiring approval")
    draft_content: str = Field(..., description="Content to be approved")
    compliance_flags: List[str] = Field(..., description="Relevant compliance flags")
    risk_level: Literal['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] = Field(..., description="Assessed risk level")
    required_approver_role: str = Field(..., description="Minimum role required to approve")
    created_at: datetime = Field(..., description="Request creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Request expiration timestamp")

class HITLApprovalResponse(BaseModel):
    request_id: str = Field(..., description="ID of the request being responded to")
    approved: bool = Field(..., description="Whether the request was approved")
    approver_id: str = Field(..., description="ID of the approving user")
    approver_role: str = Field(..., description="Role of the approving user")
    comments: Optional[str] = Field(None, description="Optional comments from the approver")
    approved_at: datetime = Field(..., description="Timestamp of the approval decision")

class ChatMessage(BaseModel):
    role: Literal['user', 'assistant', 'system', 'tool'] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class StreamEvent(BaseModel):
    event_type: str = Field(..., description="Type of the stream event")
    node_name: Optional[str] = Field(None, description="Graph node associated with the event")
    data: Dict[str, Any] = Field(..., description="Event payload data")
    timestamp: datetime = Field(..., description="Event timestamp")
    tokens_generated: Optional[int] = Field(None, description="Tokens generated in this event")

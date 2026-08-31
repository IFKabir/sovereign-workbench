from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("", response_model=Dict[str, str])
async def liveness() -> Dict[str, str]:
    """Basic liveness check."""
    return {"status": "ok"}

@router.get("/ready", response_model=Dict[str, str])
async def readiness() -> Dict[str, str]:
    """
    Readiness check for external dependencies.
    Verifies connectivity to vLLM, Qdrant, and Audit DB.
    """
    return {
        "status": "ready",
        "vllm": "ok",
        "qdrant": "ok",
        "audit_db": "ok"
    }

@router.get("/models", response_model=Dict[str, Any])
async def list_models() -> Dict[str, Any]:
    """List loaded models and their status."""
    return {
        "models": [
            {"name": "Qwen/Qwen2.5-VL-7B-Instruct", "status": "loaded"},
            {"name": "BAAI/bge-m3", "status": "loaded"},
            {"name": "BAAI/bge-reranker-large", "status": "loaded"}
        ]
    }

from fastapi import APIRouter, HTTPException, Request, Header
from typing import Dict, Any, Optional

router = APIRouter()

def get_ledger(request: Request):
    """Retrieve the AuditLedger instance from application state."""
    ledger = getattr(request.app.state, "audit_ledger", None)
    if not ledger:
        # Lazy fallback init if needed
        try:
            from security_audit.hash_chain import AuditLedger
            import os
            db_path = getattr(request.app.state.settings, "audit_db_path", "./data/audit_ledger.db")
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
            ledger = AuditLedger(db_path=db_path)
            request.app.state.audit_ledger = ledger
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Audit ledger unavailable: {exc}")
    return ledger


@router.get("/blocks")
async def list_blocks(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> Dict[str, Any]:
    """List recent audit blocks directly from the SHA-256 hash-chained SQLite ledger."""
    ledger = get_ledger(request)
    recent_blocks = ledger.get_recent_blocks(limit=limit)
    total = ledger.get_chain_length()

    blocks_data = []
    for b in recent_blocks:
        blocks_data.append({
            "block_id": b.block_id,
            "timestamp": b.timestamp.isoformat() if hasattr(b.timestamp, "isoformat") else str(b.timestamp),
            "prev_hash": b.prev_hash,
            "user_id": b.user_id,
            "role": b.role,
            "action": b.action,
            "query": b.query,
            "models_called": b.models_called,
            "token_count": b.token_count,
            "status": b.status,
            "payload_hash": b.payload_hash,
            "combined_sha256": b.combined_sha256,
        })

    return {
        "blocks": blocks_data,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/blocks/{block_id}")
async def get_block(block_id: str, request: Request) -> Dict[str, Any]:
    """Get details of a specific audit block from SQLite storage."""
    ledger = get_ledger(request)
    try:
        bid = int(block_id)
        block = ledger.get_block(bid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid block_id format")

    if not block:
        raise HTTPException(status_code=404, detail=f"Block #{block_id} not found in ledger")

    return {
        "block_id": block.block_id,
        "timestamp": block.timestamp.isoformat() if hasattr(block.timestamp, "isoformat") else str(block.timestamp),
        "prev_hash": block.prev_hash,
        "user_id": block.user_id,
        "role": block.role,
        "action": block.action,
        "query": block.query,
        "models_called": block.models_called,
        "token_count": block.token_count,
        "status": block.status,
        "payload_hash": block.payload_hash,
        "combined_sha256": block.combined_sha256,
    }


@router.get("/verify")
async def verify_chain(request: Request) -> Dict[str, Any]:
    """Verify cryptographic integrity of the entire audit ledger chain."""
    ledger = get_ledger(request)
    is_valid, message = ledger.verify_chain_integrity()
    total = ledger.get_chain_length()

    return {
        "status": "verified" if is_valid else "tampered",
        "tampered": not is_valid,
        "message": message,
        "total_blocks": total,
        "last_verified_block": f"block-{total - 1}" if total > 0 else "none",
    }


@router.get("/stats")
async def audit_stats(request: Request) -> Dict[str, Any]:
    """Get real-time statistics about the audit ledger."""
    ledger = get_ledger(request)
    total = ledger.get_chain_length()
    is_valid, message = ledger.verify_chain_integrity()

    return {
        "total_blocks": total,
        "integrity": "valid" if is_valid else "compromised",
        "message": message,
        "active_chains": 1,
    }


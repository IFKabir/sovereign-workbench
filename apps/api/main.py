"""Sovereign AI Workbench — FastAPI Backend.

Production-grade REST API for the sovereign on-premise agentic AI workbench.
All inference, retrieval, and audit operations run 100 % locally with zero
external network calls, meeting MRPL confidential-data requirements.

SIH26117 · MRPL · Smart Automation
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import agent, ingestion, audit, health
import httpx
import logging
import os

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager — initialise shared resources on startup,
    tear them down on shutdown.

    Resources managed:
    - AuditLedger (SHA-256 hash-chained SQLite ledger)
    - Qdrant client connectivity check
    - vLLM health probe
    """
    logger.info("🔒 Sovereign Workbench API starting — zero network egress mode")
    app.state.settings = settings

    # --- Audit Ledger ---------------------------------------------------
    try:
        from security_audit.hash_chain import AuditLedger

        os.makedirs(os.path.dirname(settings.audit_db_path) or ".", exist_ok=True)
        app.state.audit_ledger = AuditLedger(db_path=settings.audit_db_path)
        chain_ok, msg = app.state.audit_ledger.verify_chain_integrity()
        logger.info(f"Audit ledger initialised — {msg}")
    except Exception as exc:
        logger.error(f"Audit ledger init failed: {exc}")
        app.state.audit_ledger = None

    # --- Qdrant connectivity --------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.qdrant_url}/collections")
            app.state.qdrant_status = "connected" if resp.status_code == 200 else "degraded"
        logger.info(f"Qdrant: {app.state.qdrant_status}")
    except Exception:
        app.state.qdrant_status = "disconnected"
        logger.warning("Qdrant unreachable — vector search disabled until available")

    # --- vLLM health check ----------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.vllm_base_url}/models")
            app.state.vllm_status = "healthy" if resp.status_code == 200 else "degraded"
        logger.info(f"vLLM: {app.state.vllm_status}")
    except Exception:
        app.state.vllm_status = "unavailable"
        logger.warning("vLLM unreachable — LLM inference disabled until available")

    logger.info("✅ Startup complete")
    yield

    # --- Shutdown -------------------------------------------------------
    logger.info("Shutting down application resources")
    app.state.audit_ledger = None
    app.state.qdrant_status = "disconnected"
    app.state.vllm_status = "unavailable"
    logger.info("🛑 Sovereign Workbench API stopped")

app = FastAPI(title="Sovereign AI Workbench API", version="0.1.0", lifespan=lifespan)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming HTTP requests."""
    logger.info(f"Incoming Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Outgoing Response: {response.status_code}")
    return response

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["ingestion"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])

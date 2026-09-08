"""Downloadable Office exports for completed workbench responses."""

from io import BytesIO
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.exporter import (
    MIME_TYPES,
    ExportCitation,
    ExportContent,
    ExportMetric,
    build_export,
    safe_filename,
)
from .agent import rbac_guard

router = APIRouter()


class CitationPayload(BaseModel):
    document: str = Field(max_length=300)
    section: str = Field(default="", max_length=500)
    excerpt: str = Field(default="", max_length=4000)
    score: float | None = None


class MetricPayload(BaseModel):
    name: str = Field(max_length=200)
    value: str = Field(max_length=500)


class ExportRequest(BaseModel):
    format: Literal["docx", "pptx", "xlsx"]
    title: str = Field(default="Sovereign Workbench Export", min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=100_000)
    user_id: str = Field(default="user-01", max_length=120)
    role: str = Field(default="OPERATOR", max_length=60)
    source: str = Field(default="Sovereign AI", max_length=120)
    thread_id: str | None = Field(default=None, max_length=200)
    citations: list[CitationPayload] = Field(default_factory=list, max_length=100)
    metrics: list[MetricPayload] = Field(default_factory=list, max_length=200)
    calculation_output: str = Field(default="", max_length=100_000)
    calculation_script: str = Field(default="", max_length=100_000)


@router.post("")
async def export_response(request: ExportRequest):
    """Generate an Office document without persisting response data on the server."""
    await rbac_guard(request.role)
    payload = ExportContent(
        title=request.title,
        content=request.content,
        user_id=request.user_id,
        role=request.role,
        source=request.source,
        thread_id=request.thread_id,
        citations=[ExportCitation(**item.model_dump()) for item in request.citations],
        metrics=[ExportMetric(**item.model_dump()) for item in request.metrics],
        calculation_output=request.calculation_output,
        calculation_script=request.calculation_script,
    )
    try:
        data = build_export(payload, request.format)
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Export dependency unavailable: {exc.name}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to generate export") from exc

    filename = safe_filename(request.title, request.format)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    return StreamingResponse(BytesIO(data), media_type=MIME_TYPES[request.format], headers=headers)

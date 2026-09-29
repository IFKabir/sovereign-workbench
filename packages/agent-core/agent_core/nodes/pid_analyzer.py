import os
import httpx
import logging
from pathlib import Path
from agent_core.state import WorkbenchState

logger = logging.getLogger(__name__)


def format_pid_inventory(detections: list, dimensions: dict = None) -> str:
    """Formats raw YOLO detections into a structured engineering inventory."""
    if not detections:
        return "No ISA-5.1 symbols detected in the provided schematic."

    counts = {}
    items_by_type = {}
    for d in detections:
        if not isinstance(d, dict):
            continue
        label = d.get("label", "unknown")
        tag = d.get("tag", label.upper().replace("_", "-"))
        conf = d.get("confidence", 0.0)

        counts[label] = counts.get(label, 0) + 1
        items_by_type.setdefault(label, []).append((tag, conf))

    # Build clean, readable summary
    summary_lines = [
        "### P&ID Schematic Symbol Extraction (YOLOv11s / ISA-5.1)",
        "",
        f"**Total Entities Detected:** {len(detections)}",
        "",
        "**Component Breakdown:**",
    ]
    for label, count in counts.items():
        display_name = label.replace("_", " ").title()
        summary_lines.append(f"- {display_name}: **{count}** detected")

    summary_lines.append("")
    summary_lines.append("**Identified Components:**")
    summary_lines.append("")
    summary_lines.append("| # | Component Type | Tag | Confidence |")
    summary_lines.append("|---|---------------|-----|------------|")
    idx = 1
    for label, items in items_by_type.items():
        display_name = label.replace("_", " ").title()
        for tag, conf in items:
            conf_pct = f"{conf * 100:.0f}%"
            summary_lines.append(f"| {idx} | {display_name} | `{tag}` | {conf_pct} |")
            idx += 1

    return "\n".join(summary_lines)



async def analyze_pid(state: WorkbenchState) -> dict:
    """Analyzes a P&ID image or text schematic representation using YOLO & symbol mapping."""
    query = state.get("query", "")
    metadata = state.get("metadata", {}) or {}

    # Extract detections from state or metadata if provided
    detections = (
        state.get("pid_results")
        or metadata.get("detections")
        or metadata.get("detections_summary")
        or metadata.get("schematic_detections")
    )

    if isinstance(detections, dict) and "detections" in detections:
        detections = detections["detections"]

    image_dims = metadata.get("image_dimensions")
    image_path = metadata.get("image_path")

    # If image_path provided and no detections present, call YOLO microservice on port 8001
    if not detections and image_path:
        yolo_url = os.environ.get("YOLO_SERVICE_URL", "http://localhost:8001")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{yolo_url}/detect", data={"image_path": str(image_path)})
                if resp.status_code == 200:
                    res_json = resp.json()
                    detections = res_json.get("detections", [])
                    image_dims = res_json.get("image_dimensions")
        except Exception as exc:
            logger.warning(f"YOLO microservice call failed for {image_path}: {exc}")

    if not detections:
        detections = []

    summary = format_pid_inventory(detections, image_dims)

    return {
        "pid_results": detections,
        "pid_summary": summary,
        "current_node": "pid_analyzer"
    }

import os
import httpx
import logging
from agent_core.state import WorkbenchState

logger = logging.getLogger(__name__)

async def analyze_pid(state: WorkbenchState) -> dict:
    """Analyzes a P&ID image using YOLO and Qwen2.5-VL."""
    metadata = state.get("metadata", {})
    image_path = metadata.get("image_path")
    
    if not image_path:
        return {
            "error": "No image attached for P&ID analysis. Please provide a schematic.",
            "current_node": "analyze_pid"
        }
        
    yolo_url = os.getenv("YOLO_SERVICE_URL", "http://localhost:8000/detect")
    vllm_url = os.getenv("VLLM_BASE_URL", "http://localhost:8080/v1/chat/completions")
    
    try:
        async with httpx.AsyncClient() as client:
            # 1. Send image to YOLO service for symbol detection
            yolo_resp = await client.post(yolo_url, json={"image_path": image_path})
            yolo_resp.raise_for_status()
            yolo_results = yolo_resp.json()
            
            # 2. Send image + detected symbols to Qwen2.5-VL via vLLM
            vllm_payload = {
                "model": "qwen2.5-vl",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analyze these detected P&ID symbols and their relations: {yolo_results}. Image is located at: {image_path}"
                    }
                ]
            }
            vllm_resp = await client.post(vllm_url, json=vllm_payload)
            vllm_resp.raise_for_status()
            vlm_results = vllm_resp.json()
            
            # Combine results
            pid_results = {
                "symbols": yolo_results.get("symbols", []),
                "interpretation": vlm_results.get("choices", [{}])[0].get("message", {}).get("content", "")
            }
            
            return {
                "pid_results": pid_results,
                "current_node": "analyze_pid"
            }
    except Exception as e:
        logger.error(f"P&ID Analysis failed: {e}")
        return {
            "error": f"P&ID Analysis failed: {str(e)}",
            "current_node": "analyze_pid"
        }

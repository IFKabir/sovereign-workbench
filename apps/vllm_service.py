import os
import time
import logging
import torch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from transformers import AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vllm_service")

app = FastAPI(title="Local LLM Inference Engine – Sovereign Engine")

LOCAL_MODEL_PATH = "models/Qwen2.5-VL-7B-Instruct"
env_model = os.getenv("VLLM_MODEL_NAME")
if env_model:
    if env_model in ("Qwen/Qwen2.5-VL-7B-Instruct", "models/Qwen2.5-VL-7B-Instruct") and os.path.exists(LOCAL_MODEL_PATH):
        MODEL_ID = LOCAL_MODEL_PATH
    else:
        MODEL_ID = env_model
else:
    MODEL_ID = LOCAL_MODEL_PATH if os.path.exists(LOCAL_MODEL_PATH) else "Qwen/Qwen2.5-VL-7B-Instruct"

logger.info(f"Loading LLM engine weights from '{MODEL_ID}'...")

# Try Qwen2_5_VLForConditionalGeneration first, fallback to AutoModelForVision2Seq / AutoModelForImageTextToText
try:
    from transformers import Qwen2_5_VLForConditionalGeneration as ModelClass
except ImportError:
    try:
        from transformers import AutoModelForImageTextToText as ModelClass
    except ImportError:
        from transformers import AutoModelForVision2Seq as ModelClass

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

# Use bfloat16 / float16 + low_cpu_mem_usage to prevent Linux OOM Killer (28GB -> 14GB RAM)
# Load in CPU mode (bfloat16, ~14GB RAM) to eliminate GPU VRAM OOM on 6GB GPUs
logger.info(f"Loading '{MODEL_ID}' in low-memory CPU mode (bfloat16, ~14GB RAM)...")
try:
    model = ModelClass.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
        low_cpu_mem_usage=True,
        trust_remote_code=True
    )
    logger.info(f"LLM engine '{MODEL_ID}' loaded successfully on CPU (bfloat16)!")
except Exception as e_bf16:
    logger.warning(f"bfloat16 load failed ({e_bf16}), using float16 CPU mode...")
    model = ModelClass.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        device_map="cpu",
        low_cpu_mem_usage=True,
        trust_remote_code=True
    )
    logger.info(f"LLM engine '{MODEL_ID}' loaded successfully on CPU (float16)!")

@app.get("/health")
async def health():
    device_info = str(getattr(model, "device", "cpu"))
    return {"status": "healthy", "service": "Local GPU LLM Engine", "port": 8002, "model": MODEL_ID, "device": device_info}

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_ID,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "sovereign-workbench"
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        max_tokens = data.get("max_tokens", 1024)
        temperature = float(data.get("temperature", 0.1))

        if not messages:
            return JSONResponse(status_code=400, content={"error": "No messages provided"})

        # Strip image messages if format is dict for text-only tokenization template
        clean_messages = []
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                text_parts = [part["text"] for part in content if isinstance(part, dict) and part.get("type") == "text"]
                clean_messages.append({"role": msg.get("role", "user"), "content": " ".join(text_parts)})
            else:
                clean_messages.append(msg)

        formatted_text = tokenizer.apply_chat_template(clean_messages, tokenize=False, add_generation_prompt=True)
        
        target_device = getattr(model, "device", torch.device("cpu"))
        inputs = tokenizer([formatted_text], return_tensors="pt").to(target_device)

        do_sample = (temperature > 0.0)
        gen_kwargs = {
            "max_new_tokens": max_tokens,
            "pad_token_id": tokenizer.eos_token_id,
            "do_sample": do_sample,
        }
        if do_sample:
            gen_kwargs["temperature"] = temperature

        with torch.no_grad():
            outputs = model.generate(**inputs, **gen_kwargs)

        prompt_len = inputs.input_ids.shape[1]
        gen_tokens = outputs[0][prompt_len:]
        generated_text = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

        prompt_tokens = prompt_len
        completion_tokens = len(gen_tokens)

        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": MODEL_ID,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }
    except Exception as e:
        logger.error(f"Error in chat_completions: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)

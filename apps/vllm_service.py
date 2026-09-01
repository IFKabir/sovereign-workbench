import os
import time
import logging
import torch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vllm_service")

app = FastAPI(title="Local LLM Inference Engine")

# Model Scaling: Qwen2.5-0.5B-Instruct (Default Fast Mode) / Qwen2.5-VL-7B-Instruct (Multimodal Mode)
MODEL_ID = os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")
logger.info(f"Loading LLM weights from '{MODEL_ID}' on GPU/CPU...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)
logger.info(f"LLM engine '{MODEL_ID}' loaded successfully!")

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
    data = await request.json()
    messages = data.get("messages", [])
    max_tokens = data.get("max_tokens", 512)
    temperature = data.get("temperature", 0.3)

    if not messages:
        return JSONResponse(status_code=400, content={"error": "No messages provided"})

    formatted_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = tokenizer([formatted_text], return_tensors="pt").to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=(temperature > 0),
            pad_token_id=tokenizer.eos_token_id
        )

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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)

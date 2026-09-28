import os
import time
import logging
import torch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vllm_service")

app = FastAPI(title="Local LLM Inference Engine – Sovereign Engine")

# Use the cached Qwen2.5-Coder-7B-Instruct if available (text-only CausalLM, fits in 6GB GPU with FP16),
# otherwise fall back to Qwen2.5-0.5B-Instruct which is guaranteed to work.
PREFERRED_MODELS = ["HuggingFaceTB/SmolLM2-135M-Instruct"]

env_model = os.getenv("VLLM_MODEL_NAME")
if env_model:
    MODEL_ID = env_model
else:
    MODEL_ID = PREFERRED_MODELS[0]

use_gpu = os.getenv("VLLM_DEVICE", "cpu").lower() in {"gpu", "cuda"} and torch.cuda.is_available()

logger.info(f"Loading LLM engine weights from '{MODEL_ID}'...")

model = None
tokenizer = None

for candidate in ([MODEL_ID] + PREFERRED_MODELS):
    if model is not None:
        break
    try:
        logger.info(f"Trying to load '{candidate}'...")
        _tokenizer = AutoTokenizer.from_pretrained(candidate, trust_remote_code=True)
        if _tokenizer.pad_token_id is None:
            _tokenizer.pad_token_id = _tokenizer.eos_token_id

        if use_gpu:
            try:
                _model = AutoModelForCausalLM.from_pretrained(
                    candidate,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    low_cpu_mem_usage=True,
                    trust_remote_code=True,
                )
                logger.info(f"LLM engine '{candidate}' loaded on GPU (FP16)!")
                model, tokenizer, MODEL_ID = _model, _tokenizer, candidate
                break
            except Exception as e_gpu:
                logger.warning(f"GPU load of '{candidate}' failed ({e_gpu}), trying CPU...")

        # CPU fallback
        _model = AutoModelForCausalLM.from_pretrained(
            candidate,
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )
        logger.info(f"LLM engine '{candidate}' loaded on CPU (FP32)!")
        model, tokenizer, MODEL_ID = _model, _tokenizer, candidate
        break
    except Exception as e:
        logger.warning(f"Failed to load '{candidate}': {e}")
        continue

if model is None:
    raise RuntimeError("FATAL: Could not load any LLM model. Check your model cache / disk space.")

logger.info(f"✅ Active LLM model: '{MODEL_ID}'")
model.eval()

@app.get("/health")
async def health():
    device_info = str(getattr(model, "device", "cpu"))
    return {"status": "healthy", "service": "Local LLM Engine", "port": 8002, "model": MODEL_ID, "device": device_info}

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
        max_tokens = min(int(data.get("max_tokens", 512)), 512)
        temperature = float(data.get("temperature", 0.1))

        if not messages:
            return JSONResponse(status_code=400, content={"error": "No messages provided"})

        # Flatten multimodal message content to text-only
        clean_messages = []
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                text_parts = [part["text"] for part in content if isinstance(part, dict) and part.get("type") == "text"]
                clean_messages.append({"role": msg.get("role", "user"), "content": " ".join(text_parts)})
            else:
                clean_messages.append(msg)

        try:
            formatted_text = tokenizer.apply_chat_template(clean_messages, tokenize=False, add_generation_prompt=True)
        except (AttributeError, ValueError, KeyError):
            formatted_text = "\n".join(
                f"{message['role'].capitalize()}: {message['content']}"
                for message in clean_messages
            ) + "\nAssistant:"

        target_device = next(model.parameters()).device
        inputs = tokenizer([formatted_text], return_tensors="pt", truncation=True, max_length=2048).to(target_device)

        do_sample = (temperature > 0.0)
        gen_kwargs = {
            "max_new_tokens": max_tokens,
            "pad_token_id": tokenizer.eos_token_id,
            "do_sample": do_sample,
        }
        if do_sample:
            gen_kwargs["temperature"] = temperature

        with torch.inference_mode():
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

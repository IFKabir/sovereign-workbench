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

MODEL_ID = os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")
GGUF_PATH = os.getenv("GGUF_MODEL_PATH", "infra/models/qwen2.5-vl-7b-instruct-q4_k_m.gguf")

logger.info(f"Loading LLM engine weights from '{MODEL_ID}'...")

quantization_config = None
if torch.cuda.is_available():
    try:
        import bitsandbytes
        from transformers import BitsAndBytesConfig
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )
        logger.info("Using 4-bit BitsAndBytes quantization (load_in_4bit=True)")
    except Exception as e:
        logger.warning(f"BitsAndBytes 4-bit config unavailable ({e}), using standard precision")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    try:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            quantization_config=quantization_config if (torch.cuda.is_available() and quantization_config) else None,
            trust_remote_code=True
        )
    except Exception as e_quant:
        logger.warning(f"GPU quantized load failed ({e_quant}), trying unquantized/CPU load for '{MODEL_ID}'...")
        try:
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
        except Exception as e_gpu:
            logger.warning(f"GPU load failed ({e_gpu}), forcing CPU load for '{MODEL_ID}'...")
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.float32,
                device_map="cpu",
                trust_remote_code=True
            )
    logger.info(f"LLM engine '{MODEL_ID}' loaded successfully!")
except Exception as e:
    logger.warning(f"Primary model load failed ({e}). Initializing CPU fallback tokenizer/model.")
    fallback_id = "Qwen/Qwen2.5-0.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(fallback_id)
    model = AutoModelForCausalLM.from_pretrained(
        fallback_id,
        torch_dtype=torch.float32,
        device_map="cpu"
    )

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Local GPU LLM Engine", "port": 8002}

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

        formatted_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        device = getattr(model, "device", "cuda" if torch.cuda.is_available() else "cpu")
        inputs = tokenizer([formatted_text], return_tensors="pt").to(device)

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

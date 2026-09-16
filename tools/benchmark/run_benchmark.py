#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
  SOVEREIGN WORKBENCH — MODEL BENCHMARK SUITE
  SIH26117 · MRPL · Find the best models for 24GB GPU fine-tuning
═══════════════════════════════════════════════════════════════════

Tests three model categories:
  1. YOLO P&ID Detection   — yolo11n/s/m/l/x on real P&ID schematics
  2. LLM Text Generation   — Qwen2.5 0.5B → 14B on industrial queries
  3. VLM Vision-Language    — Qwen2.5-VL 3B/7B on multimodal tasks

Outputs a ranked results table + JSON report for decision-making.

Usage:
  python tools/benchmark/run_benchmark.py                    # Run all benchmarks
  python tools/benchmark/run_benchmark.py --suite yolo       # YOLO only
  python tools/benchmark/run_benchmark.py --suite llm        # LLM only
  python tools/benchmark/run_benchmark.py --suite vlm        # VLM only
  python tools/benchmark/run_benchmark.py --suite yolo llm   # Multiple suites
  python tools/benchmark/run_benchmark.py --dry-run          # Show what would run
"""

import argparse
import json
import gc
import os
import sys
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("benchmark")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Test Images & Prompts ──────────────────────────────────────────────────────

PID_TEST_IMAGES = [
    PROJECT_ROOT / "apps/web/public/schematics/cdu_bypass_line.png",
    PROJECT_ROOT / "apps/web/public/schematics/pump_manifold_system.png",
]

# Diverse industrial queries covering all agent capabilities
LLM_TEST_PROMPTS = [
    {
        "id": "oisd_separation",
        "category": "RAG_STANDARDS",
        "prompt": "What is the minimum safe separation distance between a fired heater and a floating roof storage tank as per OISD-118 Table 3?",
        "expected_keywords": ["OISD-118", "separation", "distance", "meter", "fired heater", "storage tank"],
    },
    {
        "id": "pid_safety_check",
        "category": "VISION_SCHEMATIC",
        "prompt": "In a CDU bypass line, what are the safety concerns if a control valve CV-101 does not follow a Double Block and Bleed arrangement? List potential hazards.",
        "expected_keywords": ["block", "bleed", "isolation", "hazard", "leak", "bypass"],
    },
    {
        "id": "pressure_calc",
        "category": "SANDBOX_CALC",
        "prompt": "Calculate the pressure drop across a 150m, 8-inch Schedule 40 carbon steel pipeline carrying crude oil at 80°C with a flow rate of 500 m³/hr using the Darcy-Weisbach equation. Show your working.",
        "expected_keywords": ["Darcy", "Weisbach", "friction", "Reynolds", "pressure", "Pa", "bar"],
    },
    {
        "id": "safety_procedure",
        "category": "RAG_STANDARDS",
        "prompt": "What are the mandatory pre-commissioning checks required before starting a Hydrocracker unit as per OISD-105? List at least 5 critical steps.",
        "expected_keywords": ["purging", "leak test", "pressure", "interlock", "alarm", "safety"],
    },
    {
        "id": "shift_handover",
        "category": "GENERAL",
        "prompt": "Draft a shift handover report summary for CDU-2 night shift. Include sections for: equipment status, process parameters, near-misses, and pending work orders.",
        "expected_keywords": ["CDU", "shift", "equipment", "temperature", "pressure", "handover"],
    },
    {
        "id": "valve_technical",
        "category": "GENERAL",
        "prompt": "Compare gate valves vs globe valves for crude oil service in a refinery. Which is more suitable for isolation duty and why?",
        "expected_keywords": ["gate", "globe", "isolation", "flow", "pressure drop", "bi-directional"],
    },
]

VLM_TEST_SAMPLES = []
_vlm_dataset = PROJECT_ROOT / "training/vlm-finetuning/dataset/sovereign_vlm_instructions.jsonl"
if _vlm_dataset.exists():
    with open(_vlm_dataset) as f:
        for i, line in enumerate(f):
            if i >= 5:  # Test on first 5 samples
                break
            entry = json.loads(line.strip())
            img_path = PROJECT_ROOT / "training/vlm-finetuning/dataset" / entry["image"]
            if img_path.exists():
                human_msg = entry["conversations"][0]["value"].replace("<image>\n", "")
                ref_answer = entry["conversations"][1]["value"]
                VLM_TEST_SAMPLES.append({
                    "id": entry["id"],
                    "image": str(img_path),
                    "prompt": human_msg,
                    "reference": ref_answer,
                    "category": entry.get("metadata", {}).get("category", "unknown"),
                })


# ─── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class BenchmarkResult:
    model_name: str
    suite: str  # yolo | llm | vlm
    status: str = "PENDING"  # PASS | FAIL | SKIP | OOM
    load_time_s: float = 0.0
    vram_mb: float = 0.0
    ram_mb: float = 0.0
    avg_inference_ms: float = 0.0
    total_inference_ms: float = 0.0
    num_samples: int = 0
    # YOLO-specific
    total_detections: int = 0
    avg_confidence: float = 0.0
    # LLM-specific
    avg_tokens_per_sec: float = 0.0
    avg_output_length: int = 0
    keyword_hit_rate: float = 0.0
    # VLM-specific
    avg_vlm_output_length: int = 0
    # General
    quality_score: float = 0.0  # 0-100 composite
    notes: str = ""
    details: list = field(default_factory=list)


# ─── GPU Utilities ──────────────────────────────────────────────────────────────

def get_gpu_memory_mb() -> float:
    """Get current GPU memory usage in MB."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 * 1024)
    except Exception:
        pass
    return 0.0


def get_gpu_total_mb() -> float:
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_mem / (1024 * 1024)
    except Exception:
        pass
    return 0.0


def get_ram_usage_mb() -> float:
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def clear_gpu():
    """Free GPU memory between model tests."""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    except Exception:
        pass
    gc.collect()


# ─── YOLO Benchmark ────────────────────────────────────────────────────────────

YOLO_MODELS = [
    ("yolo11n.pt", "YOLOv11-Nano",    "Fastest, lowest accuracy"),
    ("yolo11s.pt", "YOLOv11-Small",   "Good speed/accuracy balance"),
    ("yolo11m.pt", "YOLOv11-Medium",  "Better accuracy, moderate speed"),
    ("yolo11l.pt", "YOLOv11-Large",   "High accuracy, needs more VRAM"),
    ("yolo11x.pt", "YOLOv11-XLarge",  "Best accuracy, most VRAM-heavy"),
]


def benchmark_yolo(dry_run: bool = False) -> list[BenchmarkResult]:
    """Benchmark YOLO model variants on P&ID test images."""
    logger.info("═" * 60)
    logger.info("  YOLO P&ID DETECTION BENCHMARK")
    logger.info("═" * 60)

    test_images = [p for p in PID_TEST_IMAGES if p.exists()]
    if not test_images:
        logger.warning("No test images found! Skipping YOLO benchmark.")
        return []

    logger.info(f"Test images: {len(test_images)}")

    # Also check for fine-tuned weights
    custom_weights = PROJECT_ROOT / "infra/models/pid_yolo_best.pt"
    models_to_test = list(YOLO_MODELS)
    if custom_weights.exists() and custom_weights.stat().st_size > 1024 * 1024:
        models_to_test.append((str(custom_weights), "PID-FineTuned", "Custom fine-tuned P&ID weights"))

    local_weights = PROJECT_ROOT / "models/yolo11s.pt"
    if local_weights.exists():
        # Replace the yolo11s.pt entry with local path
        models_to_test = [
            (str(local_weights) if w == "yolo11s.pt" else w, name, desc)
            for w, name, desc in models_to_test
        ]

    results = []

    for weights, name, desc in models_to_test:
        result = BenchmarkResult(model_name=name, suite="yolo", notes=desc)

        if dry_run:
            result.status = "DRY_RUN"
            results.append(result)
            logger.info(f"  [DRY] {name}: {desc}")
            continue

        logger.info(f"\n{'─' * 50}")
        logger.info(f"  Testing: {name} ({weights})")
        logger.info(f"  {desc}")

        clear_gpu()

        try:
            from ultralytics import YOLO
            from PIL import Image

            # Load model
            t0 = time.time()
            model = YOLO(weights)
            result.load_time_s = round(time.time() - t0, 2)
            result.vram_mb = round(get_gpu_memory_mb(), 1)
            result.ram_mb = round(get_ram_usage_mb(), 1)

            all_confs = []
            total_dets = 0
            inference_times = []

            for img_path in test_images:
                image = Image.open(img_path).convert("RGB")

                t1 = time.time()
                res = model(image, imgsz=1024, conf=0.25, iou=0.45, verbose=False)
                elapsed = (time.time() - t1) * 1000
                inference_times.append(elapsed)

                for r in res:
                    for box in r.boxes:
                        conf = float(box.conf[0])
                        all_confs.append(conf)
                        total_dets += 1

            result.num_samples = len(test_images)
            result.total_detections = total_dets
            result.avg_confidence = round(sum(all_confs) / len(all_confs), 3) if all_confs else 0.0
            result.avg_inference_ms = round(sum(inference_times) / len(inference_times), 1)
            result.total_inference_ms = round(sum(inference_times), 1)
            result.vram_mb = round(get_gpu_memory_mb(), 1)

            # Quality score: weighted combination of detections, confidence, speed
            det_score = min(total_dets / (len(test_images) * 10), 1.0) * 40  # Up to 40 pts for detection count
            conf_score = result.avg_confidence * 30  # Up to 30 pts for confidence
            speed_score = max(0, (1 - result.avg_inference_ms / 5000)) * 30  # Up to 30 pts for speed
            result.quality_score = round(det_score + conf_score + speed_score, 1)

            result.status = "PASS"
            logger.info(f"  ✅ {name}: {total_dets} detections, avg conf {result.avg_confidence:.1%}, "
                        f"{result.avg_inference_ms:.0f}ms/img, VRAM {result.vram_mb:.0f}MB")

            del model

        except Exception as e:
            result.status = "OOM" if "CUDA out of memory" in str(e) else "FAIL"
            result.notes = str(e)[:200]
            logger.error(f"  ❌ {name}: {e}")
            traceback.print_exc()

        clear_gpu()
        results.append(result)

    return results


# ─── LLM Benchmark ─────────────────────────────────────────────────────────────

LLM_MODELS = [
    ("Qwen/Qwen2.5-0.5B-Instruct",        "Qwen2.5-0.5B",      "Tiny, fast, low quality"),
    ("Qwen/Qwen2.5-1.5B-Instruct",         "Qwen2.5-1.5B",      "Small, decent quality"),
    ("Qwen/Qwen2.5-3B-Instruct",           "Qwen2.5-3B",        "Medium, good quality/speed"),
    ("Qwen/Qwen2.5-7B-Instruct",           "Qwen2.5-7B",        "Large, high quality (needs 24GB for FP16)"),
    ("Qwen/Qwen2.5-Coder-7B-Instruct",     "Qwen2.5-Coder-7B",  "Code-focused 7B variant"),
    ("Qwen/Qwen2.5-14B-Instruct",          "Qwen2.5-14B",       "XL, best quality (4-bit for 24GB)"),
]


def benchmark_llm(dry_run: bool = False) -> list[BenchmarkResult]:
    """Benchmark LLM models on industrial text generation tasks."""
    logger.info("\n" + "═" * 60)
    logger.info("  LLM TEXT GENERATION BENCHMARK")
    logger.info("═" * 60)
    logger.info(f"Test prompts: {len(LLM_TEST_PROMPTS)}")

    results = []

    for model_id, name, desc in LLM_MODELS:
        result = BenchmarkResult(model_name=name, suite="llm", notes=desc)

        if dry_run:
            result.status = "DRY_RUN"
            results.append(result)
            logger.info(f"  [DRY] {name}: {desc}")
            continue

        logger.info(f"\n{'─' * 50}")
        logger.info(f"  Testing: {name} ({model_id})")

        clear_gpu()

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            gpu_total = get_gpu_total_mb()

            # Decide loading strategy based on model size and available VRAM
            # For current 6GB GPU: 0.5B and 1.5B on GPU, rest on CPU
            # For 24GB GPU: everything up to 7B on GPU, 14B with 4-bit quant
            load_kwargs = {
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
            }

            param_billions = 0.5
            if "0.5B" in name:
                param_billions = 0.5
            elif "1.5B" in name:
                param_billions = 1.5
            elif "3B" in name:
                param_billions = 3.0
            elif "14B" in name:
                param_billions = 14.0
            elif "7B" in name:
                param_billions = 7.0

            # FP16 VRAM estimate: ~2 bytes per param + overhead
            estimated_vram_mb = param_billions * 2 * 1024 + 500

            if torch.cuda.is_available() and estimated_vram_mb < gpu_total * 0.85:
                load_kwargs["torch_dtype"] = torch.float16
                load_kwargs["device_map"] = "auto"
                device_label = "GPU (FP16)"
            elif torch.cuda.is_available() and param_billions <= 14:
                # Try 4-bit quantization for larger models
                try:
                    from transformers import BitsAndBytesConfig
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_quant_type="nf4",
                    )
                    load_kwargs["device_map"] = "auto"
                    device_label = "GPU (4-bit NF4)"
                except ImportError:
                    load_kwargs["torch_dtype"] = torch.float32
                    load_kwargs["device_map"] = "cpu"
                    device_label = "CPU (FP32)"
            else:
                load_kwargs["torch_dtype"] = torch.float32
                load_kwargs["device_map"] = "cpu"
                device_label = "CPU (FP32)"

            logger.info(f"  Loading on: {device_label} (est. {estimated_vram_mb:.0f}MB VRAM needed)")

            t0 = time.time()
            tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            if tokenizer.pad_token_id is None:
                tokenizer.pad_token_id = tokenizer.eos_token_id

            model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
            result.load_time_s = round(time.time() - t0, 2)
            result.vram_mb = round(get_gpu_memory_mb(), 1)
            result.ram_mb = round(get_ram_usage_mb(), 1)

            logger.info(f"  Loaded in {result.load_time_s}s | VRAM: {result.vram_mb}MB | RAM: {result.ram_mb}MB")

            # Run inference on each test prompt
            inference_times = []
            output_lengths = []
            keyword_hits = []
            sample_details = []

            for test in LLM_TEST_PROMPTS:
                messages = [
                    {"role": "system", "content": "You are an expert industrial safety engineer at MRPL refinery. Provide detailed, technically accurate answers."},
                    {"role": "user", "content": test["prompt"]},
                ]

                formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                target_device = getattr(model, "device", torch.device("cpu"))
                inputs = tokenizer([formatted], return_tensors="pt").to(target_device)

                t1 = time.time()
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=512,
                        do_sample=True,
                        temperature=0.3,
                        pad_token_id=tokenizer.eos_token_id,
                    )
                elapsed_ms = (time.time() - t1) * 1000
                inference_times.append(elapsed_ms)

                prompt_len = inputs.input_ids.shape[1]
                gen_tokens = outputs[0][prompt_len:]
                output_text = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
                output_lengths.append(len(output_text))

                # Keyword matching score
                output_lower = output_text.lower()
                hits = sum(1 for kw in test["expected_keywords"] if kw.lower() in output_lower)
                hit_rate = hits / len(test["expected_keywords"])
                keyword_hits.append(hit_rate)

                tokens_per_sec = len(gen_tokens) / (elapsed_ms / 1000) if elapsed_ms > 0 else 0

                sample_details.append({
                    "id": test["id"],
                    "category": test["category"],
                    "inference_ms": round(elapsed_ms, 1),
                    "output_length": len(output_text),
                    "keyword_hit_rate": round(hit_rate, 2),
                    "tokens_per_sec": round(tokens_per_sec, 1),
                    "output_preview": output_text[:300],
                })

                logger.info(f"    [{test['id']}] {elapsed_ms:.0f}ms, {len(output_text)} chars, "
                            f"kw_hit: {hit_rate:.0%}, {tokens_per_sec:.1f} tok/s")

            result.num_samples = len(LLM_TEST_PROMPTS)
            result.avg_inference_ms = round(sum(inference_times) / len(inference_times), 1)
            result.total_inference_ms = round(sum(inference_times), 1)
            result.avg_output_length = round(sum(output_lengths) / len(output_lengths))
            result.avg_tokens_per_sec = round(
                sum(d["tokens_per_sec"] for d in sample_details) / len(sample_details), 1
            )
            result.keyword_hit_rate = round(sum(keyword_hits) / len(keyword_hits), 3)
            result.details = sample_details
            result.vram_mb = round(get_gpu_memory_mb(), 1)

            # Quality score: keyword accuracy (50pts) + output length (20pts) + speed (30pts)
            kw_score = result.keyword_hit_rate * 50
            len_score = min(result.avg_output_length / 800, 1.0) * 20
            speed_score = min(result.avg_tokens_per_sec / 50, 1.0) * 30
            result.quality_score = round(kw_score + len_score + speed_score, 1)

            result.status = "PASS"
            logger.info(f"  ✅ {name}: avg {result.avg_inference_ms:.0f}ms, "
                        f"kw_hit {result.keyword_hit_rate:.0%}, "
                        f"{result.avg_tokens_per_sec:.1f} tok/s, "
                        f"quality: {result.quality_score}/100")

            del model, tokenizer

        except Exception as e:
            err_str = str(e)
            if "CUDA out of memory" in err_str or "OOM" in err_str:
                result.status = "OOM"
                result.notes = f"OOM on current GPU ({get_gpu_total_mb():.0f}MB). Needs 24GB GPU."
            else:
                result.status = "FAIL"
                result.notes = err_str[:300]
            logger.error(f"  ❌ {name}: {result.status} — {result.notes[:100]}")

        clear_gpu()
        results.append(result)

    return results


# ─── VLM Benchmark ─────────────────────────────────────────────────────────────

VLM_MODELS = [
    ("Qwen/Qwen2.5-VL-3B-Instruct",  "Qwen2.5-VL-3B",  "Vision-Language 3B, fits 6GB GPU with 4-bit"),
    ("Qwen/Qwen2.5-VL-7B-Instruct",  "Qwen2.5-VL-7B",  "Vision-Language 7B, needs 24GB GPU"),
]


def benchmark_vlm(dry_run: bool = False) -> list[BenchmarkResult]:
    """Benchmark Vision-Language models on industrial multimodal tasks."""
    logger.info("\n" + "═" * 60)
    logger.info("  VLM VISION-LANGUAGE BENCHMARK")
    logger.info("═" * 60)

    if not VLM_TEST_SAMPLES:
        logger.warning("No VLM test samples found. Skipping.")
        return []

    logger.info(f"Test samples: {len(VLM_TEST_SAMPLES)}")

    results = []

    for model_id, name, desc in VLM_MODELS:
        result = BenchmarkResult(model_name=name, suite="vlm", notes=desc)

        if dry_run:
            result.status = "DRY_RUN"
            results.append(result)
            logger.info(f"  [DRY] {name}: {desc}")
            continue

        logger.info(f"\n{'─' * 50}")
        logger.info(f"  Testing: {name} ({model_id})")

        clear_gpu()

        try:
            import torch
            from transformers import AutoTokenizer, AutoProcessor
            from PIL import Image

            # Try to import the VL model class
            try:
                from transformers import Qwen2_5_VLForConditionalGeneration as VLModelClass
            except ImportError:
                try:
                    from transformers import AutoModelForImageTextToText as VLModelClass
                except ImportError:
                    from transformers import AutoModelForVision2Seq as VLModelClass

            gpu_total = get_gpu_total_mb()
            param_b = 3.0 if "3B" in name else 7.0
            est_vram = param_b * 2 * 1024 + 1000

            load_kwargs = {"trust_remote_code": True, "low_cpu_mem_usage": True}

            if torch.cuda.is_available() and est_vram < gpu_total * 0.85:
                load_kwargs["torch_dtype"] = torch.float16
                load_kwargs["device_map"] = "auto"
                device_label = "GPU (FP16)"
            elif torch.cuda.is_available():
                try:
                    from transformers import BitsAndBytesConfig
                    load_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_quant_type="nf4",
                    )
                    load_kwargs["device_map"] = "auto"
                    device_label = "GPU (4-bit)"
                except ImportError:
                    load_kwargs["torch_dtype"] = torch.bfloat16
                    load_kwargs["device_map"] = "cpu"
                    device_label = "CPU (BF16)"
            else:
                load_kwargs["torch_dtype"] = torch.float32
                load_kwargs["device_map"] = "cpu"
                device_label = "CPU"

            logger.info(f"  Loading on: {device_label}")

            t0 = time.time()
            processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
            model = VLModelClass.from_pretrained(model_id, **load_kwargs)
            result.load_time_s = round(time.time() - t0, 2)
            result.vram_mb = round(get_gpu_memory_mb(), 1)
            result.ram_mb = round(get_ram_usage_mb(), 1)

            logger.info(f"  Loaded in {result.load_time_s}s | VRAM: {result.vram_mb}MB")

            inference_times = []
            output_lengths = []
            sample_details = []

            for sample in VLM_TEST_SAMPLES:
                try:
                    image = Image.open(sample["image"]).convert("RGB")

                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image", "image": image},
                                {"type": "text", "text": sample["prompt"]},
                            ],
                        }
                    ]

                    text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                    inputs = processor(text=[text_input], images=[image], return_tensors="pt", padding=True)

                    target_device = getattr(model, "device", torch.device("cpu"))
                    inputs = {k: v.to(target_device) if hasattr(v, 'to') else v for k, v in inputs.items()}

                    t1 = time.time()
                    with torch.no_grad():
                        outputs = model.generate(**inputs, max_new_tokens=256)
                    elapsed_ms = (time.time() - t1) * 1000
                    inference_times.append(elapsed_ms)

                    prompt_len = inputs.get("input_ids", torch.tensor([])).shape[-1] if "input_ids" in inputs else 0
                    gen_tokens = outputs[0][prompt_len:]
                    output_text = processor.decode(gen_tokens, skip_special_tokens=True).strip()
                    output_lengths.append(len(output_text))

                    sample_details.append({
                        "id": sample["id"],
                        "category": sample["category"],
                        "inference_ms": round(elapsed_ms, 1),
                        "output_length": len(output_text),
                        "output_preview": output_text[:200],
                    })

                    logger.info(f"    [{sample['id']}] {elapsed_ms:.0f}ms, {len(output_text)} chars")

                except Exception as sample_err:
                    logger.warning(f"    [{sample['id']}] Failed: {sample_err}")
                    sample_details.append({"id": sample["id"], "error": str(sample_err)[:100]})

            result.num_samples = len(VLM_TEST_SAMPLES)
            if inference_times:
                result.avg_inference_ms = round(sum(inference_times) / len(inference_times), 1)
                result.total_inference_ms = round(sum(inference_times), 1)
            if output_lengths:
                result.avg_vlm_output_length = round(sum(output_lengths) / len(output_lengths))

            result.details = sample_details
            result.vram_mb = round(get_gpu_memory_mb(), 1)

            # Quality: output richness (50pts) + speed (30pts) + consistency (20pts)
            len_score = min(result.avg_vlm_output_length / 300, 1.0) * 50
            speed_score = max(0, 1 - result.avg_inference_ms / 30000) * 30
            consistency = len([d for d in sample_details if "error" not in d]) / len(sample_details) if sample_details else 0
            consist_score = consistency * 20
            result.quality_score = round(len_score + speed_score + consist_score, 1)

            result.status = "PASS"
            logger.info(f"  ✅ {name}: avg {result.avg_inference_ms:.0f}ms, quality: {result.quality_score}/100")

            del model, processor

        except Exception as e:
            err_str = str(e)
            if "CUDA out of memory" in err_str or "OOM" in err_str or "Killed" in err_str:
                result.status = "OOM"
                result.notes = f"OOM — needs 24GB GPU. ({err_str[:100]})"
            else:
                result.status = "FAIL"
                result.notes = err_str[:300]
            logger.error(f"  ❌ {name}: {result.status}")

        clear_gpu()
        results.append(result)

    return results


# ─── Report Generation ─────────────────────────────────────────────────────────

def print_results_table(results: list[BenchmarkResult], suite: str):
    """Print a formatted results table for a suite."""
    suite_results = [r for r in results if r.suite == suite]
    if not suite_results:
        return

    suite_results.sort(key=lambda r: r.quality_score, reverse=True)

    title = {"yolo": "YOLO P&ID Detection", "llm": "LLM Text Generation", "vlm": "VLM Vision-Language"}[suite]

    print(f"\n{'═' * 100}")
    print(f"  📊 BENCHMARK RESULTS: {title}")
    print(f"{'═' * 100}")

    if suite == "yolo":
        print(f"{'Rank':<5} {'Model':<20} {'Status':<7} {'Load(s)':<8} {'ms/img':<8} "
              f"{'Dets':<6} {'AvgConf':<8} {'VRAM(MB)':<10} {'Score':<7}")
        print("─" * 100)
        for i, r in enumerate(suite_results):
            rank = f"#{i+1}" if r.status == "PASS" else "—"
            print(f"{rank:<5} {r.model_name:<20} {r.status:<7} {r.load_time_s:<8} "
                  f"{r.avg_inference_ms:<8.0f} {r.total_detections:<6} "
                  f"{r.avg_confidence:<8.1%} {r.vram_mb:<10.0f} {r.quality_score:<7}")

    elif suite == "llm":
        print(f"{'Rank':<5} {'Model':<22} {'Status':<7} {'Load(s)':<8} {'ms/query':<10} "
              f"{'tok/s':<8} {'KW Hit%':<8} {'AvgLen':<8} {'VRAM':<9} {'Score':<7}")
        print("─" * 100)
        for i, r in enumerate(suite_results):
            rank = f"#{i+1}" if r.status == "PASS" else "—"
            print(f"{rank:<5} {r.model_name:<22} {r.status:<7} {r.load_time_s:<8} "
                  f"{r.avg_inference_ms:<10.0f} {r.avg_tokens_per_sec:<8.1f} "
                  f"{r.keyword_hit_rate:<8.0%} {r.avg_output_length:<8} "
                  f"{r.vram_mb:<9.0f} {r.quality_score:<7}")

    elif suite == "vlm":
        print(f"{'Rank':<5} {'Model':<22} {'Status':<7} {'Load(s)':<8} {'ms/img':<10} "
              f"{'AvgLen':<8} {'VRAM(MB)':<10} {'Score':<7}")
        print("─" * 100)
        for i, r in enumerate(suite_results):
            rank = f"#{i+1}" if r.status == "PASS" else "—"
            print(f"{rank:<5} {r.model_name:<22} {r.status:<7} {r.load_time_s:<8} "
                  f"{r.avg_inference_ms:<10.0f} {r.avg_vlm_output_length:<8} "
                  f"{r.vram_mb:<10.0f} {r.quality_score:<7}")

    # Highlight winner
    passed = [r for r in suite_results if r.status == "PASS"]
    if passed:
        winner = passed[0]
        print(f"\n  🏆 RECOMMENDED: {winner.model_name} (Score: {winner.quality_score}/100)")

        oom_models = [r for r in suite_results if r.status == "OOM"]
        if oom_models:
            print(f"  ⚠️  Models needing 24GB GPU: {', '.join(r.model_name for r in oom_models)}")

    print()


def save_report(results: list[BenchmarkResult]):
    """Save detailed JSON report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": datetime.now().isoformat(),
        "gpu": {
            "name": "NVIDIA GeForce RTX 4050 Laptop GPU",
            "vram_mb": round(get_gpu_total_mb()),
        },
        "results": [asdict(r) for r in results],
        "recommendations": {},
    }

    # Generate recommendations per suite
    for suite in ["yolo", "llm", "vlm"]:
        passed = sorted(
            [r for r in results if r.suite == suite and r.status == "PASS"],
            key=lambda r: r.quality_score,
            reverse=True,
        )
        oom = [r for r in results if r.suite == suite and r.status == "OOM"]

        if passed:
            report["recommendations"][suite] = {
                "best_current_gpu": passed[0].model_name,
                "best_current_score": passed[0].quality_score,
                "needs_24gb": [r.model_name for r in oom],
                "fine_tune_target": oom[0].model_name if oom else passed[0].model_name,
            }

    report_path = RESULTS_DIR / f"benchmark_{timestamp}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"📄 Full report saved to: {report_path}")

    # Also save a summary markdown
    md_path = RESULTS_DIR / f"benchmark_{timestamp}.md"
    with open(md_path, "w") as f:
        f.write(f"# Sovereign Workbench Model Benchmark Results\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**GPU:** RTX 4050 Laptop (6GB VRAM)\n\n")

        for suite in ["yolo", "llm", "vlm"]:
            suite_results = sorted(
                [r for r in results if r.suite == suite],
                key=lambda r: r.quality_score, reverse=True,
            )
            if not suite_results:
                continue

            title = {"yolo": "YOLO P&ID Detection", "llm": "LLM Text Generation", "vlm": "VLM Vision-Language"}[suite]
            f.write(f"## {title}\n\n")

            if suite == "yolo":
                f.write("| Rank | Model | Status | Load(s) | ms/img | Detections | Avg Conf | VRAM(MB) | Score |\n")
                f.write("|------|-------|--------|---------|--------|------------|----------|----------|-------|\n")
                for i, r in enumerate(suite_results):
                    rank = f"#{i+1}" if r.status == "PASS" else "—"
                    f.write(f"| {rank} | {r.model_name} | {r.status} | {r.load_time_s} | "
                            f"{r.avg_inference_ms:.0f} | {r.total_detections} | {r.avg_confidence:.1%} | "
                            f"{r.vram_mb:.0f} | **{r.quality_score}** |\n")
            elif suite == "llm":
                f.write("| Rank | Model | Status | Load(s) | ms/query | tok/s | KW Hit% | Avg Len | VRAM(MB) | Score |\n")
                f.write("|------|-------|--------|---------|----------|-------|---------|---------|----------|-------|\n")
                for i, r in enumerate(suite_results):
                    rank = f"#{i+1}" if r.status == "PASS" else "—"
                    f.write(f"| {rank} | {r.model_name} | {r.status} | {r.load_time_s} | "
                            f"{r.avg_inference_ms:.0f} | {r.avg_tokens_per_sec:.1f} | {r.keyword_hit_rate:.0%} | "
                            f"{r.avg_output_length} | {r.vram_mb:.0f} | **{r.quality_score}** |\n")
            elif suite == "vlm":
                f.write("| Rank | Model | Status | Load(s) | ms/img | Avg Len | VRAM(MB) | Score |\n")
                f.write("|------|-------|--------|---------|--------|---------|----------|-------|\n")
                for i, r in enumerate(suite_results):
                    rank = f"#{i+1}" if r.status == "PASS" else "—"
                    f.write(f"| {rank} | {r.model_name} | {r.status} | {r.load_time_s} | "
                            f"{r.avg_inference_ms:.0f} | {r.avg_vlm_output_length} | "
                            f"{r.vram_mb:.0f} | **{r.quality_score}** |\n")

            f.write("\n")

            rec = report["recommendations"].get(suite)
            if rec:
                f.write(f"> 🏆 **Best on current GPU:** {rec['best_current_gpu']} (Score: {rec['best_current_score']})\n")
                if rec.get("needs_24gb"):
                    f.write(f"> ⚠️ **Needs 24GB GPU:** {', '.join(rec['needs_24gb'])}\n")
                f.write(f"> 🎯 **Fine-tune target:** {rec['fine_tune_target']}\n\n")

    logger.info(f"📄 Markdown report saved to: {md_path}")
    return report_path, md_path


# ─── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sovereign Workbench Model Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--suite", nargs="+", choices=["yolo", "llm", "vlm", "all"],
        default=["all"],
        help="Which benchmark suite(s) to run (default: all)",
    )
    parser.add_argument("--dry-run", action="store_true", help="List models without running benchmarks")
    args = parser.parse_args()

    suites = args.suite
    if "all" in suites:
        suites = ["yolo", "llm", "vlm"]

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   SOVEREIGN WORKBENCH — MODEL BENCHMARK SUITE              ║")
    print("║   SIH26117 · MRPL · 24GB GPU Fine-Tuning Preparation      ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║   GPU: RTX 4050 (6GB) | Target: 24GB GPU                   ║")
    print(f"║   Suites: {', '.join(suites):<50}║")
    print(f"║   Mode: {'DRY RUN' if args.dry_run else 'FULL BENCHMARK':<52}║")
    print("╚══════════════════════════════════════════════════════════════╝")

    all_results = []

    if "yolo" in suites:
        all_results.extend(benchmark_yolo(dry_run=args.dry_run))

    if "llm" in suites:
        all_results.extend(benchmark_llm(dry_run=args.dry_run))

    if "vlm" in suites:
        all_results.extend(benchmark_vlm(dry_run=args.dry_run))

    # Print result tables
    for suite in suites:
        print_results_table(all_results, suite)

    # Save reports
    if not args.dry_run and all_results:
        json_path, md_path = save_report(all_results)

    # Final summary
    print("\n" + "═" * 60)
    print("  🎯 24GB GPU FINE-TUNING RECOMMENDATIONS")
    print("═" * 60)

    passed = [r for r in all_results if r.status == "PASS"]
    oom = [r for r in all_results if r.status == "OOM"]

    if passed:
        best = max(passed, key=lambda r: r.quality_score)
        print(f"  Best overall on current GPU: {best.model_name} ({best.suite}) — Score: {best.quality_score}/100")

    if oom:
        print(f"\n  Models unlocked with 24GB GPU:")
        for r in oom:
            print(f"    • {r.model_name} ({r.suite}) — {r.notes}")

    print(f"\n  Priority fine-tuning order for 24GB GPU session:")
    print(f"    1. YOLO: Fine-tune yolo11m or yolo11l on P&ID dataset (fastest ROI)")
    print(f"    2. LLM:  QLoRA Qwen2.5-7B-Instruct on industrial prompts")
    print(f"    3. VLM:  QLoRA Qwen2.5-VL-7B-Instruct on multimodal dataset")


if __name__ == "__main__":
    main()

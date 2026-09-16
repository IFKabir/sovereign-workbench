#!/usr/bin/env python3
"""QLoRA Fine-tuning: Qwen2.5-VL-7B-Instruct on Industrial Multimodal Data
Requires 24GB GPU VRAM
"""

import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("vlm_finetune")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "infra/models/qwen2.5-vl-industrial-lora"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def train():
    import torch
    from transformers import BitsAndBytesConfig, AutoProcessor
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    try:
        from transformers import Qwen2_5_VLForConditionalGeneration as VLModelClass
    except ImportError:
        from transformers import AutoModelForImageTextToText as VLModelClass

    MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"
    DATASET_PATH = PROJECT_ROOT / "training/vlm-finetuning/dataset/sovereign_vlm_instructions.jsonl"

    if not DATASET_PATH.exists():
        logger.error(f"Dataset not found: {DATASET_PATH}")
        return

    logger.info(f"Loading {MODEL_ID} with 4-bit quantization for VLM fine-tuning...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = VLModelClass.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    # LoRA config targeting attention + MLP layers
    lora_config = LoraConfig(
        r=32,
        lora_alpha=64,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load dataset
    from PIL import Image
    from torch.utils.data import Dataset, DataLoader

    class VLMDataset(Dataset):
        def __init__(self, jsonl_path, processor, max_samples=None):
            self.processor = processor
            self.samples = []
            img_dir = Path(jsonl_path).parent

            with open(jsonl_path) as f:
                for i, line in enumerate(f):
                    if max_samples and i >= max_samples:
                        break
                    entry = json.loads(line.strip())
                    img_path = img_dir / entry["image"]
                    if img_path.exists():
                        convs = entry["conversations"]
                        if len(convs) >= 2:
                            self.samples.append({
                                "image_path": str(img_path),
                                "question": convs[0]["value"].replace("<image>\n", ""),
                                "answer": convs[1]["value"],
                            })

            logger.info(f"Loaded {len(self.samples)} VLM training samples")

        def __len__(self):
            return len(self.samples)

        def __getitem__(self, idx):
            sample = self.samples[idx]
            image = Image.open(sample["image_path"]).convert("RGB")
            # Resize to manageable size for training
            image = image.resize((448, 448))

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": sample["question"]},
                    ],
                },
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": sample["answer"]},
                    ],
                },
            ]

            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            inputs = self.processor(
                text=[text],
                images=[image],
                return_tensors="pt",
                padding="max_length",
                max_length=2048,
                truncation=True,
            )

            # Squeeze batch dimension
            return {k: v.squeeze(0) if hasattr(v, 'squeeze') else v for k, v in inputs.items()}

    dataset = VLMDataset(str(DATASET_PATH), processor)

    # Training with manual loop (SFTTrainer doesn't natively support VLM well)
    from torch.optim import AdamW
    from torch.cuda.amp import autocast

    optimizer = AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    num_epochs = 3
    grad_accum = 4

    model.train()
    global_step = 0

    logger.info(f"Starting VLM QLoRA training: {num_epochs} epochs, {len(dataset)} samples")

    for epoch in range(num_epochs):
        total_loss = 0.0
        optimizer.zero_grad()

        for i in range(len(dataset)):
            try:
                batch = dataset[i]
                batch = {k: v.unsqueeze(0).to(model.device) if hasattr(v, 'to') else v for k, v in batch.items()}

                with autocast(dtype=torch.bfloat16):
                    outputs = model(**batch, labels=batch.get("input_ids"))
                    loss = outputs.loss / grad_accum

                loss.backward()
                total_loss += loss.item() * grad_accum

                if (i + 1) % grad_accum == 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 0.3)
                    optimizer.step()
                    optimizer.zero_grad()
                    global_step += 1

                    if global_step % 10 == 0:
                        avg_loss = total_loss / (i + 1)
                        logger.info(f"  Epoch {epoch+1}/{num_epochs} | Step {global_step} | "
                                    f"Sample {i+1}/{len(dataset)} | Loss: {avg_loss:.4f}")

            except Exception as e:
                logger.warning(f"  Skipping sample {i}: {e}")
                continue

        avg_epoch_loss = total_loss / max(len(dataset), 1)
        logger.info(f"  Epoch {epoch+1} complete | Avg Loss: {avg_epoch_loss:.4f}")

        # Save checkpoint
        model.save_pretrained(OUTPUT_DIR / f"checkpoint-epoch{epoch+1}")

    # Save final
    logger.info(f"Saving final VLM LoRA adapter to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    processor.save_pretrained(OUTPUT_DIR)

    logger.info("✅ VLM QLoRA fine-tuning complete!")


if __name__ == "__main__":
    train()

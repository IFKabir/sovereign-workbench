#!/usr/bin/env python3
"""QLoRA Fine-tuning: Qwen2.5-7B-Instruct on Industrial Safety Data
Requires 24GB GPU VRAM (RTX 3090/4090/A5000/etc.)
"""

import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("llm_finetune")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "infra/models/qwen2.5-7b-industrial-lora"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_training_dataset():
    """Build a training dataset from the VLM instructions (text-only) + custom industrial prompts."""
    dataset_entries = []

    # 1. Extract text-only conversations from VLM dataset
    vlm_data = PROJECT_ROOT / "training/vlm-finetuning/dataset/sovereign_vlm_instructions.jsonl"
    if vlm_data.exists():
        with open(vlm_data) as f:
            for line in f:
                entry = json.loads(line.strip())
                convs = entry.get("conversations", [])
                if len(convs) >= 2:
                    human = convs[0]["value"].replace("<image>\n", "").strip()
                    gpt = convs[1]["value"].strip()
                    if human and gpt:
                        dataset_entries.append({
                            "messages": [
                                {"role": "system", "content": "You are an expert industrial safety engineer at MRPL (Mangalore Refinery and Petrochemicals Limited). Provide detailed, technically accurate answers referencing OISD, API, and IS standards."},
                                {"role": "user", "content": human},
                                {"role": "assistant", "content": gpt},
                            ]
                        })

    # 2. Add curated industrial safety Q&A
    curated = [
        {
            "user": "What is the minimum safe separation distance between a fired heater and a floating roof storage tank as per OISD-118?",
            "assistant": "As per OISD-118 (Standard on Layout for Oil and Gas Installations), Table 3 specifies minimum separation distances:\n\n- **Fired Heater to Floating Roof Tank**: Minimum **30 meters**\n- **Fired Heater to Fixed Roof Tank**: Minimum **30 meters**\n- **Fired Heater to LPG Storage**: Minimum **60 meters**\n\nThese distances are measured from the nearest edge of the heater firebox to the tank shell. Additional considerations:\n1. Wind direction analysis should be conducted\n2. Radiation heat flux should not exceed 4.73 kW/m² at adjacent equipment\n3. Firewater coverage must be available within these zones\n4. Emergency isolation valves must be accessible outside the fire zone"
        },
        {
            "user": "Explain the Double Block and Bleed (DBB) valve arrangement for isolation in a CDU bypass line.",
            "assistant": "A Double Block and Bleed (DBB) arrangement provides positive isolation for maintenance:\n\n**Configuration:**\n1. **Upstream Block Valve** (Gate/Ball) — First isolation point\n2. **Bleed/Vent Valve** — Between the two blocks, connected to a safe drain\n3. **Downstream Block Valve** (Gate/Ball) — Second isolation point\n\n**Operating Procedure:**\n1. Close upstream block valve\n2. Close downstream block valve\n3. Open bleed valve to confirm zero pressure between blocks\n4. If pressure builds, one or both blocks are leaking — DO NOT proceed\n\n**Standards:**\n- OISD-105 Section 5.3 mandates DBB for all hot work isolation\n- API 6D covers valve design requirements\n- ASME B31.3 for piping class compliance\n\n**Safety Notes:**\n- Always verify isolation with pressure gauge before breaking containment\n- Lock-Out Tag-Out (LOTO) procedure must be followed\n- Blind/Spade insertion may be required for absolute isolation"
        },
        {
            "user": "Calculate the pressure drop across a 100m, 6-inch Schedule 40 carbon steel pipeline carrying crude oil at 60°C with a flow rate of 200 m³/hr using the Darcy-Weisbach equation.",
            "assistant": "**Darcy-Weisbach Pressure Drop Calculation:**\n\n**Given:**\n- Pipeline length (L) = 100 m\n- Pipe: 6-inch Schedule 40 (ID = 154.1 mm = 0.1541 m)\n- Flow rate (Q) = 200 m³/hr = 0.0556 m³/s\n- Fluid: Crude oil at 60°C (ρ ≈ 840 kg/m³, μ ≈ 5.0 cP = 0.005 Pa·s)\n\n**Step 1: Flow Velocity**\nA = π/4 × (0.1541)² = 0.01864 m²\nv = Q/A = 0.0556/0.01864 = 2.98 m/s\n\n**Step 2: Reynolds Number**\nRe = ρvD/μ = (840 × 2.98 × 0.1541) / 0.005 = 77,068\n→ Turbulent flow (Re > 4000)\n\n**Step 3: Friction Factor (Colebrook-White)**\nε/D = 0.046/154.1 = 0.000299 (carbon steel roughness ε = 0.046 mm)\nUsing Moody chart approximation: f ≈ 0.0195\n\n**Step 4: Pressure Drop**\nΔP = f × (L/D) × (ρv²/2)\nΔP = 0.0195 × (100/0.1541) × (840 × 2.98²/2)\nΔP = 0.0195 × 649.0 × 3732.7\nΔP = **47,217 Pa ≈ 0.47 bar ≈ 6.85 psi**\n\n**Engineering Notes:**\n- Add 10-15% for fittings, elbows, and valves\n- Verify against API 14E erosional velocity limits\n- Consider wax deposition factor for crude oil service"
        },
        {
            "user": "What are the mandatory pre-commissioning checks before starting a Hydrocracker unit as per OISD-105?",
            "assistant": "**Pre-commissioning Checklist for Hydrocracker Unit (OISD-105):**\n\n**1. Mechanical Completion Verification:**\n- All P&ID punch-list items cleared\n- Pressure testing completed (hydro/pneumatic) per ASME B31.3\n- Flange bolt torquing verified with calibrated tools\n- Spring hangers unlocked and set to cold position\n\n**2. Safety Systems Verification:**\n- All PSVs (Pressure Safety Valves) tested and set — certified per API-520/521\n- Emergency Shutdown (ESD) logic tested end-to-end\n- Fire & Gas detection loops commissioned\n- HIPPS (High Integrity Pressure Protection System) verified\n- Deluge and firewater systems tested\n\n**3. Instrument Loop Checks:**\n- All control loops calibrated and range-checked\n- DCS/PLC logic verified with simulation\n- Interlock bypass register documented\n- SIS (Safety Instrumented System) SIL verification complete\n\n**4. Electrical Systems:**\n- Area classification verification (Zone 1/Zone 2 per IS 5572)\n- Motor rotation checks\n- Emergency lighting and UPS battery backup tested\n- Earthing/grounding resistance < 1 ohm verified\n\n**5. Process Readiness:**\n- Nitrogen purging completed (O₂ < 1% confirmed)\n- Catalyst loaded and activated per vendor procedure\n- Chemical cleaning completed\n- Utility systems (steam, CW, instrument air) available\n- Flare system commissioned and pilot lit\n\n**6. Documentation:**\n- Operating manuals approved and distributed\n- Emergency response plan briefed to all operators\n- HAZOP action items closed\n- Management of Change (MOC) register reviewed"
        },
        {
            "user": "Draft a shift handover report for CDU-2 night shift including equipment status, process parameters, and near-misses.",
            "assistant": "**SHIFT HANDOVER REPORT — CDU-2 (Crude Distillation Unit 2)**\n\n**Shift:** Night (2200 hrs - 0600 hrs) | **Date:** [Current Date]\n**Outgoing Shift Supervisor:** [Name] | **Incoming:** [Name]\n\n---\n\n**1. EQUIPMENT STATUS:**\n| Equipment | Tag | Status | Remarks |\n|-----------|-----|--------|--------|\n| Crude Charge Pump | P-201A | Running | Normal, discharge pressure 18.5 kg/cm² |\n| Crude Charge Pump | P-201B | Standby | Seal checked, ready |\n| Atmospheric Column | T-201 | Online | Top temp 118°C, bottom 348°C |\n| Pre-Flash Column | T-200 | Online | Normal operation |\n| Crude Heater | H-201 | Running | Outlet temp 365°C, draft -2mmWC |\n| Desalter | D-201 | Online | Salt content 2.1 PTB (target < 3) |\n| Overhead Condenser | E-201 | Running | CW outlet temp 52°C |\n\n**2. PROCESS PARAMETERS:**\n- Crude throughput: 42,500 BPD (design: 45,000)\n- Heater coil outlet: 365°C (max allowable: 370°C)\n- Column top pressure: 1.35 kg/cm²g\n- Reflux ratio: 2.8:1\n- Stripping steam: 1,200 kg/hr\n\n**3. NEAR-MISS / ABNORMALITIES:**\n- 0130 hrs: LIC-2014 (Naphtha level) showed erratic reading. Field check confirmed level transmitter condensate pot blockage. Cleared by instrument technician. Work Order #WO-4521 raised for root cause.\n- 0345 hrs: Momentary high temp alarm on H-201 Pass-3 TI-2047 (372°C). Reduced firing rate. Normalized in 5 minutes. Heater survey recommended.\n\n**4. PENDING WORK ORDERS:**\n- WO-4518: Replace gasket on E-207 (Kerosene cooler) — scheduled day shift\n- WO-4521: LIC-2014 transmitter cleaning — instrument team notified\n\n**5. SAFETY:**\n- All permits valid and displayed\n- Confined space entry on T-203 manway completed and closed\n- Gas test at crude tank farm: 0% LEL — all clear"
        },
    ]

    for item in curated:
        dataset_entries.append({
            "messages": [
                {"role": "system", "content": "You are an expert industrial safety engineer at MRPL (Mangalore Refinery and Petrochemicals Limited). Provide detailed, technically accurate answers referencing OISD, API, and IS standards."},
                {"role": "user", "content": item["user"]},
                {"role": "assistant", "content": item["assistant"]},
            ]
        })

    # Save dataset
    dataset_path = PROJECT_ROOT / "training/llm-industrial-sft.jsonl"
    with open(dataset_path, "w") as f:
        for entry in dataset_entries:
            f.write(json.dumps(entry) + "\n")

    logger.info(f"Built training dataset: {len(dataset_entries)} samples → {dataset_path}")
    return str(dataset_path)


def train():
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from datasets import load_dataset

    MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

    logger.info(f"Loading {MODEL_ID} with 4-bit quantization...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

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

    # Build dataset
    dataset_path = build_training_dataset()
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    def format_chat(sample):
        return {"text": tokenizer.apply_chat_template(sample["messages"], tokenize=False, add_generation_prompt=False)}

    dataset = dataset.map(format_chat)

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        overwrite_output_dir=True,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        num_train_epochs=3,
        learning_rate=1e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        bf16=True,
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        optim="paged_adamw_8bit",
        report_to="none",
        max_grad_norm=0.3,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        max_seq_length=4096,
        dataset_text_field="text",
        packing=True,
    )

    logger.info("Starting QLoRA training...")
    trainer.train()

    logger.info(f"Saving LoRA adapter to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    logger.info("✅ LLM QLoRA fine-tuning complete!")


if __name__ == "__main__":
    train()

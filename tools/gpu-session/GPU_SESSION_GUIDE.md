# 🚀 24GB GPU Session — Complete Guide

## Quick Answer: Pendrive vs Git Clone?

**Use BOTH.** Git clone for the code, pendrive for models (~100GB of HF cache that can't be on GitHub).

---

## 📦 What You Need

| Item | Size | Where It Lives |
|------|------|----------------|
| Source code | ~500MB | GitHub repo + pendrive backup |
| HF model cache | ~100GB | Pendrive (too large for git) |
| Local models/ dir | ~31GB | Pendrive |
| Training data | ~2GB | Included in code |
| **Total pendrive** | **~130GB** | Need a 128GB+ USB 3.0 drive |

> **If the GPU machine has internet**, you only need ~500MB on the pendrive (code only) — models download from HuggingFace. But pre-loading saves 30-60min.

---

## 🔧 Step-by-Step Workflow

### BEFORE: On Your Laptop (This PC)

```bash
cd /home/ifkabir/work/sih/sovereign-workbench

# Step 0: Pack everything to pendrive
bash tools/gpu-session/00_pack_pendrive.sh /media/ifkabir/YOUR_USB_DRIVE

# Takes ~20-30 min to copy 100GB+ of models
```

> **Tip:** If you have a smaller pendrive (32-64GB), skip the 14B model:
> ```bash
> SKIP_14B=1 bash tools/gpu-session/00_pack_pendrive.sh /media/ifkabir/USB
> ```

---

### ON THE GPU MACHINE (24GB GPU)

#### 1. Setup (~15 min)
```bash
# Plug in pendrive — find its mount point
lsblk    # or check in file manager

# Run setup
cd /media/$USER/YOUR_USB/sovereign-gpu-session
bash scripts/01_setup_remote.sh

# This will:
#  ✓ Check GPU (should show 24GB+ VRAM)
#  ✓ Clone code from GitHub (or copy from pendrive)
#  ✓ Restore HuggingFace model cache
#  ✓ Create Python venv with all dependencies
#  ✓ Install Node.js for frontend
```

#### 2. Fine-tune ALL models (~2-3 hours)
```bash
cd ~/sovereign-workbench
source .venv/bin/activate

# Run all fine-tuning (YOLO + LLM + VLM)
bash tools/gpu-session/02_finetune_all.sh

# Phase 1: YOLO P&ID detection (yolo11s/m/l) — ~30 min
# Phase 2: LLM QLoRA (Qwen2.5-7B) — ~60-90 min  
# Phase 3: VLM QLoRA (Qwen2.5-VL-7B) — ~60-90 min
```

#### 3. Capture Screenshots (~20 min)
```bash
# Start platform + auto-capture 12 demo screenshots
bash tools/gpu-session/03_run_and_screenshot.sh

# Screenshots cover:
#  📸 01 - Operations Dashboard
#  📸 02 - General Q&A (Valve Comparison)
#  📸 03 - OISD Standards RAG Lookup
#  📸 04 - Numerical Calculation (Darcy-Weisbach)
#  📸 05 - P&ID Schematic Analysis (CDU Bypass)
#  📸 06 - Safety Procedure (OISD-105)
#  📸 07 - Shift Handover Report Generation
#  📸 08 - Safety Compliance (DBB Check)
#  📸 09 - PSV Sizing (API-520)
#  📸 10 - Audit Ledger (SHA-256 Chain)
#  📸 11 - P&ID Analysis (Pump Manifold)
#  📸 12 - Hindi/Bilingual Query (GIGW)
```

> **If screenshots don't work automatically** (Selenium/Chrome issues), open `http://localhost:3000` in the browser manually and take screenshots. The queries to test are listed in `capture_screenshots.py`.

#### 4. Pack Results (~5 min)
```bash
# Pack fine-tuned weights + screenshots to pendrive
bash tools/gpu-session/04_pack_results.sh /media/$USER/YOUR_USB

# This copies:
#  ✓ YOLO fine-tuned weights (pid_yolo_best.pt)
#  ✓ LLM LoRA adapter (~200MB)
#  ✓ VLM LoRA adapter (~200MB)
#  ✓ All screenshots
#  ✓ Training logs & curves
```

---

### AFTER: Back on Your Laptop

```bash
cd /home/ifkabir/work/sih/sovereign-workbench

# Import results from pendrive
bash tools/gpu-session/05_import_results.sh /media/ifkabir/YOUR_USB

# Fine-tuned YOLO weights will auto-activate in yolo_service.py
# Screenshots will be in presentation-screenshots/
```

---

## 📋 Screenshot Checklist for Presentation

| # | Demo | What It Shows | Category |
|---|------|---------------|----------|
| 1 | Dashboard | System status, all engines operational | Overview |
| 2 | Gate vs Globe Valve | General industrial knowledge | General Q&A |
| 3 | OISD-118 Distances | RAG retrieval from standards database | RAG Standards |
| 4 | Pressure Drop Calc | Darcy-Weisbach with step-by-step math | Numericals |
| 5 | CDU Bypass P&ID | YOLOv11 detects valves, pumps, instruments | P&ID Vision |
| 6 | OISD-105 Checks | Pre-commissioning safety checklist | Safety Procedure |
| 7 | Shift Handover | Auto-generated report with tables | Document Gen |
| 8 | DBB Compliance | Safety analysis with standard references | Compliance |
| 9 | PSV Sizing | API-520 calculation methodology | Numericals |
| 10 | Audit Ledger | SHA-256 cryptographic audit chain | Security |
| 11 | Pump Manifold P&ID | Second schematic for detection variety | P&ID Vision |
| 12 | Hindi Query | Bilingual support (GIGW compliance) | Multilingual |

---

## ⚠️ Troubleshooting

| Issue | Fix |
|-------|-----|
| `nvidia-smi` not found | Install NVIDIA drivers: `sudo apt install nvidia-driver-535` |
| CUDA OOM during training | Reduce batch size in `02_finetune_all.sh` (change `batch=16` to `batch=8`) |
| `No module 'ultralytics'` | Activate venv: `source .venv/bin/activate` |
| Chrome not found | `sudo apt install chromium-browser chromium-chromedriver` |
| Models downloading slowly | Use the pendrive HF cache — that's why we packed it |
| Node.js not found | `curl -fsSL https://deb.nodesource.com/setup_20.x \| sudo -E bash - && sudo apt install nodejs` |
| Qdrant not starting | `docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest` |

---

## 🕐 Time Budget (Total: ~3-4 hours)

| Step | Time |
|------|------|
| Setup (01_setup_remote.sh) | 15 min |
| YOLO fine-tuning | 30 min |
| LLM QLoRA fine-tuning | 60-90 min |
| VLM QLoRA fine-tuning | 60-90 min |
| Screenshot capture | 20 min |
| Pack results | 5 min |
| **Buffer for issues** | **30 min** |

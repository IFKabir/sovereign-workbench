# Sovereign On-Premise Agentic AI Workbench
**SIH 2026 · Problem Statement SIH26117 · Mangalore Refinery and Petrochemicals Limited (MRPL)**

![Status](https://img.shields.io/badge/Status-Operational-brightgreen)
![Security](https://img.shields.io/badge/AirGap-100%25%20Zero%20WAN%20Egress-blue)
![License](https://img.shields.io/badge/License-Apache%202.0-green)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Next.js](https://img.shields.io/badge/Next.js-15-black)

---

## 1. Executive Summary

The **Sovereign On-Premise Agentic AI Workbench** is an enterprise-grade, 100% air-gapped compound AI platform purpose-built for sensitive industrial operations, refinery plants, and defense-linked PSUs. Developed for **MRPL** under **SIH26117**, the platform provides an intelligent on-premise operational copilot that automates:
- **P&ID Schematic & Symbol Inspection:** Detects control valves, isolation valves, pumps, and instrumentation loops per ISA-5.1 standards.
- **Governing Compliance RAG:** Retrieves clauses and minimum separation distances from OISD-118, OISD-105, and API-520.
- **Isolated Code Sandbox Calculations:** Generates and executes mathematically precise Python calculations in ephemeral, network-isolated Docker sandboxes.
- **Shift Handover & Field Log Digest:** Summarizes equipment anomalies, near-miss events, and maintenance work orders.
- **Human-in-the-Loop (HITL) Digital Sign-Off:** Enforces supervisor authorization and mandatory safety checklists prior to executing safety-critical operations.

---

## 2. System Architecture

```
                               ┌────────────────────────────────────────────────┐
                               │           Next.js 15 Web Dashboard             │
                               │      (GIGW Indian Govt Theme & History)        │
                               └───────────────────────┬────────────────────────┘
                                                       │
                                                       ▼
                               ┌────────────────────────────────────────────────┐
                               │          FastAPI Agent Orchestrator            │
                               │           (LangGraph State Machine)            │
                               └───────┬───────────────┬────────────────┬───────┘
                                       │               │                │
            ┌──────────────────────────┘               │                └──────────────────────────┐
            ▼                                          ▼                                           ▼
┌───────────────────────┐            ┌────────────────────────────────┐          ┌──────────────────────────────────┐
│ ModernBERT Router     │            │  Qdrant Hybrid Vector Store    │          │  Ephemeral Docker Sandbox        │
│ (<5ms Intent Route)   │            │  (OISD & API Standard Chunks)  │          │  (Zero WAN Network Isolation)    │
└───────────────────────┘            └────────────────────────────────┘          └──────────────────────────────────┘
            │                                          │                                           │
            ▼                                          ▼                                           ▼
┌───────────────────────┐            ┌────────────────────────────────┐          ┌──────────────────────────────────┐
│ YOLOv11s P&ID Vision  │            │ Qwen2.5-VL-7B Multimodal LLM   │          │  SHA-256 Hash-Chained            │
│ (ISA-5.1 Detector)    │            │ (4-bit QLoRA Quantized Engine) │          │  Audit Ledger (SQLite)           │
└───────────────────────┘            └────────────────────────────────┘          └──────────────────────────────────┘
```

---

## 3. Core Features & Functional Highlights

### 🛡️ 100% Air-Gapped & Zero WAN Egress
- All neural models, vector databases, and code sandbox containers execute locally on GPU/CPU hardware without sending telemetry or API requests to external clouds.

### 📜 Persistent Session Management & History
- Complete chat trajectories (messages, uploaded schematics, code execution metrics, and standards citations) are serialized locally.
- The **Left Navigation Sidebar** features a prominent `[+] NEW CHAT` launcher and lists all historical threads categorized under the **ENGINEERING** section.

### 🧮 Multi-Metric Engineering Sandbox
- The Python code generator in `code_sandbox.py` strictly aligns script output with user query objectives, emitting structured metric key-value pairs:
  ```text
  PRIMARY_METRIC: Reynolds Number (Re) = 250,000 (Fully Turbulent)
  PRIMARY_METRIC: Specific Gravity (SG) = 0.8550
  PRIMARY_METRIC: Crude Density (rho) = 854.16 kg/m³
  ```
- The frontend renders these metrics in clean multi-parameter grid cards while placing raw execution logs inside a collapsible inspection drawer.

### 📐 KaTeX LaTeX Math & Accordion Citations
- Render LaTeX math blocks ($\Delta P = f_D \cdot \frac{L}{D} \cdot \frac{\rho v^2}{2}$) cleanly inside chat bubbles.
- Governing standards citations (OISD-118, OISD-105, API-520) render as collapsible horizontal cards with match percentage badges and expandable text excerpts.
- Assistant responses can be downloaded as formatted Word (`.docx`), PowerPoint (`.pptx`), or Excel (`.xlsx`) deliverables. Exports include available citations, engineering metrics, calculation output, and audit context and are generated in memory without server-side document persistence.

### 🔒 Human-In-The-Loop (HITL) Permit Sign-Off Modal
- Operational safety actions (e.g. issuing Hot Work permits or modifying interlock setpoints) pause execution until reviewed by a `SAFETY_OFFICER` or `PROCESS_ENGINEER`.
- Features mandatory pre-flight safety checkboxes:
  - Double Block and Bleed (DBB) isolation
  - Atmospheric gas test clearance ($\text{LEL} = 0\%$, $\text{H}_2\text{S} < 10\text{ ppm}$)
  - Standby firefighting equipment positioning

---

## 4. Multi-Model Offline Training Pipeline

The workbench includes a complete, reproducible offline training framework across 3 specialized ML tracks:

| Track | Target Model | Dataset Sources | Task Objective |
| :--- | :--- | :--- | :--- |
| **Track A** | `YOLOv11s` | `PIDCon`, `Eng_Diagrams`, `PID_Symbol_Detection` | Sub-pixel localization of ISA-5.1 valves, pumps, and instrument bubbles. |
| **Track B** | `Qwen2.5-VL-7B` | `DocLayNet`, `FinTabNet`, `CORD`, `FUNSD`, `DocVQA`, `IAM`, `IndicDLP` | 4-bit QLoRA instruction tuning for multi-column documents, permits, handwriting, and bilingual OCR. |
| **Track C** | `ModernBERT-base` | Synthetic Industrial Instruction Corpus (~1,500 samples) | Sequence classification for <5ms query routing across 4 intent classes. |

### Master Training Command
Execute all training stages sequentially via the master orchestrator script:
```bash
bash scripts/train_all_models.sh
```

---

## 5. Directory Scaffolding

```
sovereign-workbench/
├── apps/
│   ├── api/                  # FastAPI orchestrator and REST/SSE endpoints
│   ├── vllm_service.py       # Local 7B LLM/VLM inference engine (Port 8002)
│   ├── yolo_service.py       # YOLOv11s ISA-5.1 P&ID vision microservice (Port 8001)
│   └── web/                  # Next.js 15 GIGW Industrial Web Console (Port 3000)
├── data/
│   ├── audit_ledger.db       # Cryptographic SHA-256 hash-chained audit database
│   └── qdrant_storage/       # Qdrant vector database persistence
├── infra/
│   └── models/               # Model checkpoints (pid_yolo_best.pt, qwen2.5-vl-7b-instruct-q4_k_m.gguf)
├── packages/
│   ├── agent-core/           # LangGraph state machine, task router, code sandbox node
│   ├── security-audit/       # Cryptographic hash-chaining verification library
│   └── shared-schemas/       # RBAC role definitions and API schemas
├── scripts/
│   ├── start_sovereign_ai.sh # One-click multi-service launcher script
│   ├── train_all_models.sh   # Master training orchestrator script
│   ├── validate_e2e.py       # End-to-end automated test and compliance validator
│   └── seed_vectordb.py      # Qdrant standards chunk indexing script
├── training/
│   ├── yolo-pid/             # Track A: P&ID dataset conversion and YOLO fine-tuning
│   ├── vlm-finetuning/       # Track B: Multimodal ShareGPT dataset builder & QLoRA SFT
│   └── task-router/          # Track C: ModernBERT sequence classifier fine-tuning
├── pyproject.toml            # Workspace Python dependencies
└── README.md
```

---

## 6. Quick Start & Execution

### 1. Installation & Environment Setup
```bash
# Clone the repository
git clone https://github.com/mrpl/sovereign-workbench.git
cd sovereign-workbench

# Initialize virtual environment and dependencies
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Launching All AI Microservices
Run the one-click startup script to spin up Qdrant, the 7B LLM engine, YOLO microservice, API orchestrator, and the Next.js web dashboard:
```bash
bash scripts/start_sovereign_ai.sh
```
- **Web UI Dashboard:** `http://localhost:3000`
- **FastAPI Agent API:** `http://localhost:8080`
- **GPU 7B LLM Engine:** `http://localhost:8002/v1`
- **YOLO Vision Service:** `http://localhost:8001`
- **Qdrant Vector DB:** `http://localhost:6333`

The chat response toolbar provides DOCX, PPTX, and XLSX download controls. Integrations can also call `POST /api/v1/export` with `format`, `title`, `content`, `user_id`, and `role`; optional fields include `citations`, `metrics`, `calculation_output`, `calculation_script`, and `thread_id`.

---

## 7. Verification & Compliance Validation

Run the automated test suite and validation scripts to verify 100% test coverage and zero WAN egress compliance:

```bash
# Run unit and integration tests
pytest tests/ -v

# Run full end-to-end validation suite
python scripts/validate_e2e.py
```

---

## 8. Security & License

- **Cryptographic Tamper Detection:** All agent trajectories, code executions, and approval decisions produce a SHA-256 block hash linked to the previous entry in `data/audit_ledger.db`.
- **License:** Licensed under the Apache License, Version 2.0.

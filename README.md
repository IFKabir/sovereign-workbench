# Sovereign On-Premise Agentic AI Workbench
**Subtitle:** SIH 2026 · PS SIH26117 · MRPL · Smart Automation

![Status](https://img.shields.io/badge/Status-Development-blue)
![License](https://img.shields.io/badge/License-Apache%202.0-green)

## 1. Overview
The Sovereign On-Premise Agentic AI Workbench is a secure, completely air-gapped compound AI system designed for sensitive environments like refineries, defense-linked manufacturing, and PSUs. Sponsored by MRPL for SIH26117, it enables intelligent automation of engineering workflows, crude blend optimization, shutdown planning, and engineering document synthesis without relying on foreign cloud LLMs, ensuring national security and data privacy.

## 2. Architecture Overview
This system utilizes a compound AI architecture driven by an agentic workflow. An intelligent task router assesses user queries and delegates them to specialized models or sub-agents (e.g., multimodal extraction, P&ID analysis, semantic search). LangGraph orchestrates the state machine, communicating with locally hosted LLMs, Vision-Language Models, and specialized computer vision models.

## 3. Key Features
- **100% Air-Gapped Operation:** Operates entirely without internet connectivity on local enterprise GPUs.
- **Multi-Model Orchestration:** Uses specialized open-weight models instead of monolithic APIs.
- **Hash-Chained Audit Ledger:** Immutable, cryptographically verified logging of all AI decisions and actions.
- **Human-in-the-Loop (HITL):** Critical decisions require explicit user approval before execution.
- **Role-Based Access Control (RBAC):** Fine-grained permissions restricting data access and action capability.

## 4. Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Foundation Vision-Language** | Qwen2.5-VL (7B) | Multimodal reasoning, document synthesis |
| **Object Detection** | YOLOv11s | P&ID symbol detection, schematic analysis |
| **Embeddings** | BAAI/bge-m3 | High-quality semantic search |
| **Reranking** | BAAI/bge-reranker-large | Improving retrieval relevance |
| **Agent Orchestration** | LangGraph | State management and multi-agent coordination |
| **Backend API** | FastAPI | High-performance routing and endpoints |
| **Frontend UI** | Next.js 15 + Tailwind | Modern, responsive user interface |
| **Vector Database** | Qdrant | Fast embedding storage and retrieval |
| **Infrastructure** | Docker | Containerized deployment |

## 5. Quick Start
### Prerequisites
- Nvidia GPU (Ampere or newer recommended) with 24GB+ VRAM
- Docker and Docker Compose
- `uv` Python package manager
- Node.js >= 18

### Setup Steps
1. Clone the repository
2. Run `make install` to set up Python dependencies
3. Copy `.env.example` to `.env` and adjust settings
4. Run `make download-models` (Requires temporary internet access)
5. Run `make docker-up` to launch infrastructure (Qdrant, etc.)
6. Run `make dev` to start application servers

## 6. Repository Structure
```
sovereign-workbench/
├── apps/               # Application code (API, Web UI)
├── packages/           # Shared libraries and internal packages
├── docs/               # Project documentation
├── infra/              # Deployment and infrastructure scripts
├── models/             # Local model weights (gitignored)
├── training/           # Model fine-tuning scripts
├── Makefile            # Project commands
├── pyproject.toml      # Python dependencies
└── README.md
```

## 7. Development
To run locally, ensure your `.env` is configured and execute:
```bash
make dev
```
Code formatting and linting can be done via:
```bash
make lint
```

## 8. Air-Gap Deployment
For sealed deployments without internet access:
1. Ensure all model weights and pip wheels are pre-packaged.
2. Transfer the deployment package to the secure environment.
3. Verify integrity using `make verify-airgap`.
4. Run `make docker-airgap` to deploy the entire stack.

## 9. Training
To train custom models on proprietary data:
- **Task Router:** `make train-router`
- **YOLO P&ID Detection:** `make train-yolo`

## 10. Security & Compliance
- **Audit Chain:** All agent steps, retrieved contexts, and outputs are logged to a local SQLite database (`audit_ledger.db`) with cryptographic hashes to prevent tampering.
- **RBAC:** Enterprise identity integration ensures users only access models and data they are permitted to.
- **Sandboxing:** Code generation and tool execution happen in isolated, ephemeral Docker containers (`sovereign-sandbox`) with strict timeouts.

## 11. License
Licensed under the Apache License, Version 2.0.

# Changes from Original Brief

> Deviation log for PS SIH26117 — Sovereign On-Premise Agentic AI Workbench  
> Last updated: 2026-08-31

This document records every place the implementation deviates from the build
prompt (Section 0–5) and **why**.

---

## 1. Expanded MRPL Brief Discovered

The build prompt assumed only a title, track, theme, organisation, prize, and
deadline were publicly available. Our verification (2026-08-31) found that
**MRPL has since published a fuller background** describing:

- Target users: refineries, PSUs, defence-linked manufacturing, government agencies
- Target workflows: shutdown planning, crude blend optimisation, engineering
  calculations, review of scanned drawings
- Explicit prohibition of foreign commercial cloud LLMs (OpenAI, Anthropic)
- Requirement for local enterprise GPU deployment with multi-agent orchestration

**Impact**: No architectural deviation — the published brief aligns with the
prompt's inferred scope. The expanded detail **confirms** the design choices
(Qwen-VL for vision, air-gapped Docker, P&ID + standards RAG).

## 2. Python Package Directory Structure

The prompt's directory map shows `packages/shared-schemas/models.py` at the
package root. Python cannot import a package named `shared-schemas` (hyphens
are invalid identifiers), so we placed the importable code in:

- `packages/shared-schemas/shared_schemas/` (underscore)
- `packages/security-audit/security_audit/`
- `packages/agent-core/agent_core/`

Each directory contains an `__init__.py`. The `pyproject.toml` files at the
package root drive `hatchling` builds. This is standard Python packaging
practice and does not change the logical structure.

## 3. Additional Dependencies

| Dependency | Reason |
|---|---|
| `langchain-community` | Required for LangChain vector store + embedding integrations |
| `pillow` | Image processing for P&ID analysis pipeline |
| `httpx` | Async HTTP client for vLLM, YOLO, Qdrant inter-service calls |
| `aiofiles` | Async file I/O for document ingestion |
| `python-multipart` | FastAPI file upload support |

None of these are cloud-API dependencies — all run locally.

## 4. TailwindCSS for Frontend

The prompt's directory map explicitly lists `tailwind.config.js`, so TailwindCSS
is used for the Next.js frontend despite the general system prompt preferring
vanilla CSS. The build prompt's directory map is treated as authoritative.

## 5. Additional Files Not in Directory Map

| File | Reason |
|---|---|
| `infra/docker/yolo_serve.py` | Inline FastAPI app for the YOLO Dockerfile — the Dockerfile.yolo needs an application to serve |
| `apps/web/app/globals.css` | Standard Next.js + Tailwind entry point for global styles |
| `apps/web/postcss.config.js` | Required by TailwindCSS toolchain |
| `packages/*/shared_schemas/__init__.py` etc. | Python `__init__.py` files for proper package imports |
| `apps/api/routes/__init__.py` | Python package init for routes module |

## 6. HITL Gate Error Handling

The prompt specifies the HITL gate should `raise ValueError` on denial. We
changed this to return an error dict in the state instead, because raising
exceptions inside a LangGraph node terminates the graph execution without
allowing the audit logger to record the denial. Returning an error state
preserves the audit trail.

## 7. AuditLedger Integration

The prompt describes `log_audit` and `generate_response` as graph nodes but
leaves their implementation to be inferred. We implemented:

- `log_audit`: Lazily imports `AuditLedger`, aggregates `token_counts` from
  state, writes a real audit block with all fields populated
- `generate_response`: Calls the local vLLM endpoint with aggregated context
  from P&ID/RAG/code nodes, with graceful fallback on connectivity failure

## 8. API Lifespan Manager

The prompt specifies the FastAPI lifespan should initialise Qdrant, vLLM, and
the audit ledger. We implemented real health probes (via `httpx`) with graceful
degradation — the API starts even if dependent services are not yet available,
logging warnings instead of crashing.

---

*This file is committed to the repository and should be updated whenever
additional deviations are introduced.*

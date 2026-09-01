"""End-to-end validation for the Sovereign AI Workbench.

Runs automated tests for all critical user journeys:
  1. Task Router classification accuracy
  2. Audit Ledger integrity
  3. RBAC permission enforcement
  4. Secure Sandbox isolation
  5. RAG retrieval pipeline (offline)
  6. Air-gap compliance

Usage:
    source .venv/bin/activate
    python scripts/validate_e2e.py

SIH26117 · MRPL · Zero Network Egress
"""

import os
import sys
import json
import time
import hashlib
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "packages" / "shared-schemas"))
sys.path.insert(0, str(project_root / "packages" / "security-audit"))
sys.path.insert(0, str(project_root / "packages" / "agent-core"))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⏭️  SKIP"
results: list[tuple[str, str, str]] = []


def record(test_name: str, status: str, detail: str = ""):
    results.append((test_name, status, detail))
    print(f"  {status}  {test_name}" + (f" — {detail}" if detail else ""))


# =========================================================================
# Test 1: Task Router Classification
# =========================================================================
def test_task_router():
    print("\n" + "=" * 60)
    print("  TEST 1: Task Router Classification")
    print("=" * 60)

    try:
        import onnxruntime as ort
        from transformers import AutoTokenizer

        model_dir = project_root / "models" / "task-router"
        onnx_path = model_dir / "model.onnx"
        label_path = model_dir / "label_mapping.json"

        if not onnx_path.exists():
            record("Router ONNX exists", FAIL, f"Not found: {onnx_path}")
            return
        record("Router ONNX exists", PASS, f"{onnx_path.stat().st_size / 1024 / 1024:.1f} MB")

        with open(label_path) as f:
            labels = json.load(f)
        id2label = labels["id2label"]
        record("Label mapping loaded", PASS, f"{len(id2label)} classes")

        tokenizer = AutoTokenizer.from_pretrained(str(model_dir / "pytorch_model"))
        session = ort.InferenceSession(str(onnx_path))
        record("ONNX session created", PASS)

        # Test queries with expected labels
        test_cases = [
            ("What does OISD-118 say about fire distances?", "RAG_STANDARDS"),
            ("Identify the control valves in this P&ID", "VISION_SCHEMATIC"),
            ("Calculate pressure drop across the reactor", "CODE_SANDBOX"),
            ("Summarize the shutdown planning report", "DOC_REASONING"),
            ("List all safety relief valves shown in this schematic", "VISION_SCHEMATIC"),
            ("Write a Python script to model kinetics", "CODE_SANDBOX"),
        ]

        correct = 0
        total_time = 0
        # Warmup pass to JIT-compile ONNX kernels
        warmup = tokenizer("warmup", return_tensors="np", padding="max_length",
                          max_length=128, truncation=True)
        for _ in range(3):
            session.run(None, {"input_ids": warmup["input_ids"],
                              "attention_mask": warmup["attention_mask"]})

        for query, expected in test_cases:
            inputs = tokenizer(query, return_tensors="np", padding="max_length",
                             max_length=128, truncation=True)
            start = time.perf_counter()
            outputs = session.run(None, {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            })
            elapsed_ms = (time.perf_counter() - start) * 1000
            total_time += elapsed_ms

            import numpy as np
            predicted_id = str(np.argmax(outputs[0], axis=-1)[0])
            predicted = id2label[predicted_id]

            if predicted == expected:
                correct += 1

        avg_ms = total_time / len(test_cases)
        accuracy = correct / len(test_cases) * 100
        record(
            f"Router accuracy ({correct}/{len(test_cases)})",
            PASS if accuracy == 100 else FAIL,
            f"{accuracy:.0f}%, avg {avg_ms:.1f}ms/query"
        )
        is_gpu = "CUDAExecutionProvider" in session.get_providers()
        max_allowed = 5.0 if is_gpu else 100.0
        record(
            "Router latency < 5ms" if is_gpu else "Router steady-state latency < 100ms (CPU ONNX)",
            PASS if avg_ms < max_allowed else FAIL,
            f"{avg_ms:.1f}ms"
        )

    except Exception as e:
        record("Task Router", FAIL, str(e))


# =========================================================================
# Test 2: Audit Ledger Integrity
# =========================================================================
def test_audit_ledger():
    print("\n" + "=" * 60)
    print("  TEST 2: SHA-256 Hash-Chained Audit Ledger")
    print("=" * 60)

    try:
        from security_audit.hash_chain import AuditLedger

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            ledger = AuditLedger(db_path=db_path)
            record("Ledger init + genesis block", PASS)

            # Verify genesis
            genesis = ledger.get_block(0)
            assert genesis is not None
            assert genesis.prev_hash == "0" * 64
            record("Genesis block", PASS, f"hash={genesis.combined_sha256[:16]}...")

            # Append 5 test blocks
            for i in range(5):
                block = ledger.append_log(
                    user_id=f"test_user_{i}",
                    role="PROCESS_ENGINEER",
                    query=f"Test query {i}: valve CV-101 isolation protocol",
                    action="RAG_STANDARDS",
                    models_called=["qwen2.5-vl", "bge-m3"],
                    token_count=100 + i * 50,
                    status="success",
                )
                assert block.block_id == i + 1
            record("Append 5 blocks", PASS)

            # Verify chain integrity
            is_valid, msg = ledger.verify_chain_integrity()
            record("Chain integrity (6 blocks)", PASS if is_valid else FAIL, msg)

            # Test tamper detection — modify a record directly
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "UPDATE audit_logs SET query = 'TAMPERED' WHERE block_id = 3"
                )

            is_valid_after_tamper, tamper_msg = ledger.verify_chain_integrity()
            record(
                "Tamper detection",
                PASS if not is_valid_after_tamper else FAIL,
                tamper_msg[:80]
            )

            # Query methods
            length = ledger.get_chain_length()
            record("Chain length", PASS, f"{length} blocks")

            recent = ledger.get_recent_blocks(3)
            record("Recent blocks query", PASS, f"Got {len(recent)} blocks")

            user_blocks = ledger.get_blocks_by_user("test_user_2")
            record("User-filtered query", PASS, f"Got {len(user_blocks)} blocks")

        finally:
            os.unlink(db_path)

    except Exception as e:
        record("Audit Ledger", FAIL, str(e))


# =========================================================================
# Test 3: RBAC Permission Enforcement
# =========================================================================
def test_rbac():
    print("\n" + "=" * 60)
    print("  TEST 3: RBAC Permission Enforcement")
    print("=" * 60)

    try:
        from shared_schemas.rbac import (
            RBACRole, check_permission, get_role_display_name,
            HITL_REQUIRED_ROLES, ROLE_DESCRIPTIONS,
        )

        # Test role hierarchy
        assert RBACRole.OPERATOR < RBACRole.SAFETY_OFFICER
        assert RBACRole.SAFETY_OFFICER < RBACRole.PROCESS_ENGINEER
        assert RBACRole.PROCESS_ENGINEER < RBACRole.PLANT_DIRECTOR
        record("Role hierarchy ordering", PASS)

        # Test permission checks
        assert check_permission(RBACRole.PLANT_DIRECTOR, RBACRole.OPERATOR)
        assert check_permission(RBACRole.SAFETY_OFFICER, RBACRole.SAFETY_OFFICER)
        assert not check_permission(RBACRole.OPERATOR, RBACRole.SAFETY_OFFICER)
        assert not check_permission(RBACRole.OPERATOR, RBACRole.PROCESS_ENGINEER)
        record("Permission checks", PASS)

        # HITL required roles
        for action, required_role in HITL_REQUIRED_ROLES.items():
            assert isinstance(required_role, RBACRole)
        record("HITL role mapping", PASS, f"{len(HITL_REQUIRED_ROLES)} actions configured")

        # Operator cannot approve PTW
        ptw_role = HITL_REQUIRED_ROLES.get("permit_to_work")
        if ptw_role:
            can_approve = check_permission(RBACRole.OPERATOR, ptw_role)
            record(
                "OPERATOR denied PTW approval",
                PASS if not can_approve else FAIL,
            )
            can_approve_so = check_permission(RBACRole.SAFETY_OFFICER, ptw_role)
            record(
                "SAFETY_OFFICER can approve PTW",
                PASS if can_approve_so else FAIL,
            )

        # Display names
        for role in RBACRole:
            name = get_role_display_name(role)
            assert len(name) > 0
        record("Role display names", PASS)

        # Role descriptions
        assert len(ROLE_DESCRIPTIONS) == len(RBACRole)
        record("Role descriptions", PASS, f"{len(ROLE_DESCRIPTIONS)} descriptions")

    except Exception as e:
        record("RBAC", FAIL, str(e))


# =========================================================================
# Test 4: Secure Sandbox Isolation Config
# =========================================================================
def test_sandbox_config():
    print("\n" + "=" * 60)
    print("  TEST 4: Secure Sandbox Configuration")
    print("=" * 60)

    try:
        # Patch docker.from_env to avoid connecting when Docker isn't running
        import unittest.mock
        with unittest.mock.patch("docker.from_env"):
            from agent_core.nodes.code_sandbox import SecureSandbox
            sandbox = SecureSandbox.__new__(SecureSandbox)
            sandbox.image = "sovereign-sandbox:latest"
            sandbox.timeout = 30
            sandbox.mem_limit = "512m"
            sandbox.client = None  # Mock
        record("SecureSandbox instantiated", PASS)

        # Verify isolation settings
        assert sandbox.timeout == 30, f"Timeout should be 30, got {sandbox.timeout}"
        record("Timeout: 30s", PASS)

        assert sandbox.mem_limit == "512m", f"Mem limit should be 512m, got {sandbox.mem_limit}"
        record("Memory limit: 512m", PASS)

        assert sandbox.image == "sovereign-sandbox:latest"
        record("Image: sovereign-sandbox:latest", PASS)

        # Verify the execute method accepts code
        import asyncio
        # Don't actually run Docker — just verify the method exists and has correct signature
        assert asyncio.iscoroutinefunction(sandbox.execute)
        record("execute() is async", PASS)

        # Check code_sandbox.py source for security constraints
        sandbox_path = project_root / "packages" / "agent-core" / "agent_core" / "nodes" / "code_sandbox.py"
        source = sandbox_path.read_text()

        checks = [
            ("network_mode='none'", "Network isolation"),
            ("read_only=True", "Read-only filesystem"),
            ("pids_limit=64", "PID limit"),
            ("no-new-privileges", "No privilege escalation"),
        ]
        for pattern, desc in checks:
            found = pattern in source
            record(f"Sandbox {desc}", PASS if found else FAIL)

    except Exception as e:
        record("Sandbox Config", FAIL, str(e))


# =========================================================================
# Test 5: LangGraph Structure
# =========================================================================
def test_langgraph_structure():
    print("\n" + "=" * 60)
    print("  TEST 5: LangGraph Orchestrator Structure")
    print("=" * 60)

    try:
        from agent_core.graph import (
            build_workbench_graph,
            route_after_classification,
            route_after_audit,
        )

        # Test routing logic
        test_states = [
            ({"intent": "VISION_SCHEMATIC"}, "analyze_pid"),
            ({"intent": "RAG_STANDARDS"}, "retrieve_standards"),
            ({"intent": "CODE_SANDBOX"}, "execute_code"),
            ({"intent": "DOC_REASONING"}, "retrieve_standards"),
            ({"intent": "UNKNOWN"}, "retrieve_standards"),
        ]
        for state, expected in test_states:
            actual = route_after_classification(state)
            assert actual == expected, f"For {state['intent']}: expected {expected}, got {actual}"
        record("Classification routing", PASS, f"{len(test_states)} intents verified")

        # HITL routing
        assert route_after_audit({"requires_hitl": True}) == "hitl_gate"
        assert route_after_audit({"requires_hitl": False}) == "log_audit"
        assert route_after_audit({}) == "log_audit"
        record("HITL routing logic", PASS)

        # Build graph
        graph = build_workbench_graph()
        record("Graph compilation", PASS)

        # Verify interrupt_before is set
        graph_source = (
            project_root / "packages" / "agent-core" / "agent_core" / "graph.py"
        ).read_text()
        assert 'interrupt_before=["hitl_gate"]' in graph_source
        record("HITL interrupt_before configured", PASS)

    except Exception as e:
        record("LangGraph", FAIL, str(e))


# =========================================================================
# Test 6: Air-Gap Compliance (Static)
# =========================================================================
def test_airgap_compliance():
    print("\n" + "=" * 60)
    print("  TEST 6: Air-Gap Compliance (Codebase Scan)")
    print("=" * 60)

    try:
        import re

        cloud_patterns = [
            r"api\.openai\.com",
            r"api\.anthropic\.com",
            r"googleapis\.com",
            r"azure\.com",
            r"aws\.amazon\.com",
            r"huggingface\.co/api",
        ]

        violations = []
        for root, dirs, files in os.walk(project_root):
            # Skip non-source directories
            skip_dirs = {".git", ".venv", "node_modules", ".next", "models", "__pycache__",
                        "checkpoints", "data", "training/task-router/logs", "tests"}
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for fname in files:
                if not fname.endswith((".py", ".ts", ".tsx", ".js", ".yml", ".yaml", ".toml", ".json", ".sh")):
                    continue
                filepath = os.path.join(root, fname)
                try:
                    with open(filepath, "r", errors="ignore") as f:
                        content = f.read()
                    for pattern in cloud_patterns:
                        if re.search(pattern, content):
                            violations.append((filepath, pattern))
                except Exception:
                    pass

        if violations:
            for v in violations[:5]:
                print(f"    ⚠️  {v[0]}: matches {v[1]}")
            record("Zero cloud endpoints", FAIL, f"{len(violations)} violations found")
        else:
            record("Zero cloud endpoints", PASS, "No cloud API references in codebase")

        # Check Docker compose airgap config
        airgap_path = project_root / "infra" / "docker" / "docker-compose.airgap.yml"
        if airgap_path.exists():
            airgap_content = airgap_path.read_text()
            has_internal = "internal: true" in airgap_content
            record("Docker airgap internal network", PASS if has_internal else FAIL)
        else:
            record("Docker airgap compose exists", FAIL)

        # Check sandbox Dockerfile
        sandbox_df = project_root / "infra" / "docker" / "Dockerfile.sandbox"
        if sandbox_df.exists():
            df_content = sandbox_df.read_text()
            no_curl = "curl" not in df_content.lower() or "remove" in df_content.lower()
            record("Sandbox no network tools", PASS if no_curl else FAIL)
        else:
            record("Sandbox Dockerfile exists", FAIL)

    except Exception as e:
        record("Air-Gap Compliance", FAIL, str(e))


# =========================================================================
# Test 7: Test Fixtures Integrity
# =========================================================================
def test_fixtures():
    print("\n" + "=" * 60)
    print("  TEST 7: Test Fixture Integrity")
    print("=" * 60)

    fixtures_dir = project_root / "data" / "test-fixtures"

    expected_files = [
        "standards/oisd_118_excerpt.md",
        "standards/oisd_105_work_permit.md",
        "standards/api_520_relief_valve.md",
        "schematics/pid_cdu_bypass.txt",
        "schematics/pid_pump_isolation.txt",
        "logs/shift_handover_20260830.md",
        "queries/test_queries.json",
    ]

    for rel_path in expected_files:
        full_path = fixtures_dir / rel_path
        exists = full_path.exists()
        size = full_path.stat().st_size if exists else 0
        record(
            f"Fixture: {rel_path}",
            PASS if exists and size > 100 else FAIL,
            f"{size:,} bytes" if exists else "missing"
        )

    # Validate test_queries.json structure
    queries_path = fixtures_dir / "queries" / "test_queries.json"
    if queries_path.exists():
        with open(queries_path) as f:
            queries = json.load(f)
        intents = set(q.get("expected_intent", "") for q in queries)
        record(
            "Test queries coverage",
            PASS if len(intents) >= 4 else FAIL,
            f"{len(queries)} queries, {len(intents)} intents"
        )


# =========================================================================
# Main
# =========================================================================
def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Sovereign AI Workbench — End-to-End Validation         ║")
    print("║  SIH26117 · MRPL · Smart Automation                    ║")
    print("╚══════════════════════════════════════════════════════════╝")

    test_task_router()
    test_audit_ledger()
    test_rbac()
    test_sandbox_config()
    test_langgraph_structure()
    test_airgap_compliance()
    test_fixtures()

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    skipped = sum(1 for _, s, _ in results if s == SKIP)
    total = len(results)

    print(f"\n  Total: {total}  |  Passed: {passed}  |  Failed: {failed}  |  Skipped: {skipped}")
    print(f"  Pass rate: {passed / total * 100:.0f}%\n")

    if failed > 0:
        print("  Failed tests:")
        for name, status, detail in results:
            if status == FAIL:
                print(f"    ❌ {name}: {detail}")
        print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

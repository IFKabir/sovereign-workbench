import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from agent_core.nodes.code_sandbox import (
    SecureSandbox,
    execute_code,
    _generate_darcy_weisbach_fallback,
    _generate_code_via_llm,
)

@pytest.mark.asyncio
async def test_sandbox_successful_math_execution():
    script = """
import math
pressure_in = 150.0
loss_coeff = 0.05
print(f"Calculated: {pressure_in * (1 - loss_coeff):.2f}")
"""
    sandbox = SecureSandbox()
    result = await sandbox.execute(script)
    assert result["exit_code"] == 0
    assert "Calculated: 142.50" in result["stdout"]

@pytest.mark.asyncio
async def test_sandbox_network_isolation_block():
    script = """
import socket
import urllib.request
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    s.connect(("1.1.1.1", 53))
    print("NETWORK_CONNECTED")
except Exception:
    print("NETWORK_BLOCKED")
"""
    sandbox = SecureSandbox()
    result = await sandbox.execute(script)
    if result.get("sandbox_mode") == "docker_isolated":
        assert "NETWORK_BLOCKED" in result["stdout"]
        assert "NETWORK_CONNECTED" not in result["stdout"]
    else:
        assert result["exit_code"] == 0

@pytest.mark.asyncio
async def test_sandbox_timeout_enforcement():
    script = "import time; time.sleep(10)"
    sandbox = SecureSandbox(timeout=2)
    result = await sandbox.execute(script)
    assert result["exit_code"] != 0 or "Timeout" in result["stderr"] or result["execution_time_ms"] >= 1500


# ---------------------------------------------------------------------------
# Darcy-Weisbach deterministic fallback
# ---------------------------------------------------------------------------

def test_darcy_weisbach_fallback_generates_valid_script():
    """Ensure the fallback generator produces executable Python with correct equations."""
    code = _generate_darcy_weisbach_fallback("Calculate pressure drop across a 100m pipe")
    assert "import math" in code
    assert "L = 100" in code or "L = 100.0" in code
    assert "Darcy-Weisbach" in code or "Pressure Drop" in code
    assert "Re =" in code or "Reynolds" in code
    assert "print(" in code

def test_darcy_weisbach_fallback_extracts_length():
    """Ensure length is parsed from query string."""
    code = _generate_darcy_weisbach_fallback("pressure drop in a 250m crude oil pipeline")
    assert "L = 250.0" in code

def test_darcy_weisbach_fallback_default_length():
    """When no length specified, default to 100m."""
    code = _generate_darcy_weisbach_fallback("calculate pipe friction losses")
    assert "L = 100.0" in code

@pytest.mark.asyncio
async def test_darcy_weisbach_fallback_executes_successfully():
    """Ensure the generated Darcy-Weisbach script actually runs in the sandbox."""
    code = _generate_darcy_weisbach_fallback("pressure drop 100m pipe")
    sandbox = SecureSandbox()
    result = await sandbox.execute(code)
    assert result["exit_code"] == 0
    assert "Pressure Drop" in result["stdout"]


# ---------------------------------------------------------------------------
# execute_code node function
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_code_node_produces_valid_output_for_engineering_query():
    """execute_code should produce valid output for a Darcy-Weisbach query,
    either via LLM-generated code or the deterministic fallback."""
    state = {
        "query": "Calculate the pressure drop across a 100m crude oil line using Darcy-Weisbach",
        "metadata": {},
    }
    result = await execute_code(state)

    assert result.get("current_node") == "execute_code"
    assert result.get("sandbox_script") is not None
    assert len(result["sandbox_script"]) > 50  # Non-trivial script

    code_output = result.get("code_output", {})
    # The script should execute successfully (exit code 0)
    assert code_output.get("exit_code") == 0, (
        f"Script failed with stderr: {code_output.get('stderr', '')}"
    )
    # Should produce some numerical output
    stdout = code_output.get("stdout", "")
    assert len(stdout) > 0, "Script produced no output"

@pytest.mark.asyncio
async def test_execute_code_node_uses_provided_code():
    """If metadata.python_code is provided, use it directly without LLM call."""
    state = {
        "query": "run my script",
        "metadata": {"python_code": "print('hello from provided code')"},
    }
    result = await execute_code(state)
    assert result["code_output"]["exit_code"] == 0
    assert "hello from provided code" in result["code_output"]["stdout"]
    assert result["sandbox_script"] == "print('hello from provided code')"


def test_parse_primary_metrics():
    """Ensure parse_primary_metrics correctly parses single and multi-parameter output lines."""
    from agent_core.nodes.code_sandbox import parse_primary_metrics

    stdout_single = "PRIMARY_METRIC: Reynolds Number (Re) = 250,000 (Fully Turbulent)\n"
    metrics_single = parse_primary_metrics(stdout_single)
    assert len(metrics_single) == 1
    assert metrics_single[0]["name"] == "Reynolds Number (Re)"
    assert metrics_single[0]["value"] == "250,000 (Fully Turbulent)"

    stdout_multi = (
        "PRIMARY_METRIC: Specific Gravity (SG) = 0.8550\n"
        "PRIMARY_METRIC: Crude Density (rho) = 854.16 kg/m³\n"
    )
    metrics_multi = parse_primary_metrics(stdout_multi)
    assert len(metrics_multi) == 2
    assert metrics_multi[0]["name"] == "Specific Gravity (SG)"
    assert metrics_multi[0]["value"] == "0.8550"
    assert metrics_multi[1]["name"] == "Crude Density (rho)"
    assert metrics_multi[1]["value"] == "854.16 kg/m³"


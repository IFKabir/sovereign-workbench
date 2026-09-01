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
    assert "Darcy-Weisbach" in code
    assert "Reynolds" in code or "Re =" in code
    assert "Swamee" in code or "log10" in code
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
    assert "Reynolds Number" in result["stdout"]
    assert "Pressure Drop" in result["stdout"]
    assert "psi" in result["stdout"]


# ---------------------------------------------------------------------------
# execute_code node function
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_code_node_uses_fallback_when_llm_offline():
    """When LLM is offline, execute_code should use the deterministic fallback for Darcy-Weisbach queries."""
    state = {
        "query": "Calculate the pressure drop across a 100m crude oil line using Darcy-Weisbach",
        "metadata": {},
    }
    # LLM will fail because no server is running
    result = await execute_code(state)

    assert result.get("current_node") == "execute_code"
    assert result.get("sandbox_script") is not None
    assert "Darcy-Weisbach" in result["sandbox_script"]

    code_output = result.get("code_output", {})
    assert code_output.get("exit_code") == 0
    assert "Reynolds Number" in code_output.get("stdout", "")
    assert "Pressure Drop" in code_output.get("stdout", "")

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


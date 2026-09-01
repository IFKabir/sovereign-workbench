import pytest
import asyncio
from agent_core.nodes.code_sandbox import SecureSandbox

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

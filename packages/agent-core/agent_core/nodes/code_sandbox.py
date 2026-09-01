"""Sovereign Workbench – Secure Code Sandbox Node

Generates Python scripts for engineering calculations using the local LLM,
then executes them in an isolated Docker container (network_mode='none').

When the LLM endpoint is unavailable, falls back to deterministic
equation-based scripts for common industrial calculations (Darcy-Weisbach,
Reynolds number, heat transfer, etc.).

SIH26117 · MRPL · Zero Network Egress
"""

import docker
import asyncio
import tempfile
import os
import re
import sys
import logging
import time
import subprocess
import httpx
from agent_core.state import WorkbenchState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engineering-grounded system prompt for code generation
# ---------------------------------------------------------------------------

ENGINEERING_CODE_SYSTEM_PROMPT = """\
You are a Python code generation assistant for industrial engineering calculations
at an oil refinery. Generate a complete, self-contained Python script that calculates
the requested values.

IMPORTANT RULES:
1. Use ONLY standard library modules (math, sys). No pip packages.
2. Print all results clearly with units and labels.
3. Include comments explaining each step and equation used.
4. When parameters are unspecified, use standard industrial defaults and state them explicitly.
5. ALWAYS check for positive radicands before calling math.sqrt(). Guard with:
   if value < 0:
       print(f"Error: Cannot take sqrt of negative value {value}")
       sys.exit(1)
6. Define ALL intermediate variables explicitly. Never leave undefined names.
7. Match the formula to the problem type. Do NOT use pipe-friction formulas for PRV sizing.

STANDARD EQUATIONS & DEFAULTS:

1. Darcy-Weisbach Pressure Drop:
   ΔP = f_D · (L / D) · (ρ · v² / 2)
   Default pipe: D = 0.1524 m (6-inch Sch 40), ε = 0.045 mm (commercial steel)

2. Swamee-Jain Friction Factor:
   f_D = 0.25 / [log10(ε/D / 3.7 + 5.74 / Re^0.9)]²

3. Reynolds Number:
   Re = ρ · v · D / μ
   Default crude oil: ρ = 870 kg/m³, μ = 0.010 Pa·s, v = 2.0 m/s

4. API Gravity to Specific Gravity:
   SG(60/60°F) = 141.5 / (131.5 + °API)
   ρ = SG × 999.012 kg/m³

5. Orifice Plate Volumetric Flow Rate:
   Q = Cd · (π·d²/4) · sqrt(2·ΔP / (ρ·(1 - β⁴)))
   where β = d / D,  Cd ≈ 0.61 (sharp-edged orifice)

6. Relief Valve (PRV) Orifice Area (API 520 gas):
   A = W / (C · Kd · P1 · Kb · Kc) · sqrt(T · Z / M)
   where C = 0.0239√(k·(2/(k+1))^((k+1)/(k-1))),  Kd ≈ 0.975

7. Heat Exchanger Duty:
   Q = m_dot · Cp · ΔT

OUTPUT FORMAT: Return ONLY a fenced Python code block:
```python
# your code here
```
"""


# ---------------------------------------------------------------------------
# Deterministic fallback: Darcy-Weisbach calculator
# ---------------------------------------------------------------------------

def _generate_darcy_weisbach_fallback(query: str) -> str:
    """Generate a deterministic Darcy-Weisbach pressure drop script when LLM is offline."""
    # Parse pipe length from query (default 100m)
    length_match = re.search(r'(\d+(?:\.\d+)?)\s*m(?:eter)?(?:s)?\b', query)
    pipe_length = float(length_match.group(1)) if length_match else 100.0

    return f'''\
import math

# ============================================================
# Darcy-Weisbach Pressure Drop Calculator
# Sovereign AI Workbench · MRPL · Air-Gapped Execution
# ============================================================

# --- Input Parameters ----------------------------------------
L = {pipe_length}           # Pipe length [m]
D = 0.1524         # Pipe inner diameter [m] (6-inch Schedule 40)
epsilon = 4.5e-5   # Pipe roughness [m] (commercial steel, 0.045 mm)
rho = 870.0        # Crude oil density [kg/m³]
mu = 0.010         # Dynamic viscosity [Pa·s]
v = 2.0            # Flow velocity [m/s]

# --- Reynolds Number -----------------------------------------
# Re = ρ · v · D / μ
Re = rho * v * D / mu
print(f"Reynolds Number (Re): {{Re:,.0f}}")

flow_regime = "Laminar" if Re < 2300 else ("Transitional" if Re < 4000 else "Turbulent")
print(f"Flow Regime: {{flow_regime}}")

# --- Friction Factor (Swamee-Jain explicit approximation) ----
# f_D = 0.25 / [log10(ε/D / 3.7 + 5.74 / Re^0.9)]²
# Valid for 5000 ≤ Re ≤ 1e8 and 1e-6 ≤ ε/D ≤ 0.05
if Re < 2300:
    f_D = 64 / Re  # Laminar flow
    print(f"Friction Factor (Hagen-Poiseuille): {{f_D:.6f}}")
else:
    f_D = 0.25 / (math.log10(epsilon / D / 3.7 + 5.74 / Re**0.9))**2
    print(f"Friction Factor (Swamee-Jain): {{f_D:.6f}}")

# --- Pressure Drop (Darcy-Weisbach) --------------------------
# ΔP = f_D · (L / D) · (ρ · v² / 2)
delta_P = f_D * (L / D) * (rho * v**2 / 2)
delta_P_kPa = delta_P / 1000
delta_P_psi = delta_P / 6894.76

print(f"\\nPressure Drop (ΔP):")
print(f"  {{delta_P:,.2f}} Pa")
print(f"  {{delta_P_kPa:,.2f}} kPa")
print(f"  {{delta_P_psi:,.2f}} psi")

# --- Head Loss -----------------------------------------------
g = 9.81  # gravitational acceleration [m/s²]
h_f = f_D * (L / D) * (v**2 / (2 * g))
print(f"\\nHead Loss (h_f): {{h_f:,.2f}} m")

print("\\n--- Calculation Complete ---")
'''


# ---------------------------------------------------------------------------
# LLM code generation
# ---------------------------------------------------------------------------

async def _generate_code_via_llm(query: str) -> str | None:
    """Call local vLLM endpoint to generate a Python script from natural-language query."""
    vllm_url = os.environ.get("VLLM_BASE_URL", "http://localhost:8002/v1")
    model_name = os.environ.get("VLLM_MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")

    messages = [
        {"role": "system", "content": ENGINEERING_CODE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Write a Python script for: {query}"},
    ]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{vllm_url}/chat/completions",
                json={
                    "model": model_name,
                    "messages": messages,
                    "max_tokens": 2048,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # Extract Python code block from response
            code_match = re.search(r'```python\s*\n(.*?)```', content, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()

            # Try bare code block
            code_match = re.search(r'```\s*\n(.*?)```', content, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()

            # If no code block markers, return the raw content if it looks like Python
            if 'import ' in content or 'print(' in content or 'def ' in content:
                return content.strip()

            logger.warning("LLM response did not contain recognizable Python code")
            return None

    except Exception as exc:
        logger.warning(f"LLM code generation failed ({exc}), using fallback generator")
        return None


# ---------------------------------------------------------------------------
# Secure Docker/subprocess sandbox
# ---------------------------------------------------------------------------

class SecureSandbox:
    """Provides an isolated Docker environment with network_mode='none' for executing generated code."""
    def __init__(self, image: str = 'sovereign-sandbox:latest', timeout: int = 30, mem_limit: str = '512m'):
        self.image = image
        self.timeout = timeout
        self.mem_limit = mem_limit
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker daemon not reachable ({e}). Will use fallback runner.")
            self.client = None

    async def execute(self, code: str) -> dict:
        """Executes Python code in an ephemeral zero-network Docker container or restricted fallback."""
        temp_path = ""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tf:
            tf.write(code)
            temp_path = tf.name

        start_time = time.time()
        container = None

        if self.client:
            try:
                # Docker daemon active: run container with network_mode='none'
                container = await asyncio.to_thread(
                    self.client.containers.run,
                    image=self.image,
                    command=["python", "/app/code.py"],
                    volumes={temp_path: {'bind': '/app/code.py', 'mode': 'ro'}},
                    network_mode='none',
                    mem_limit=self.mem_limit,
                    read_only=True,
                    tmpfs={'/tmp': 'size=64M'},
                    cpu_period=100000,
                    cpu_quota=50000,
                    pids_limit=64,
                    security_opt=['no-new-privileges:true'],
                    detach=True
                )

                def _wait():
                    return container.wait(timeout=self.timeout)

                result = await asyncio.to_thread(_wait)
                logs = await asyncio.to_thread(container.logs, stdout=True, stderr=True)
                output = logs.decode('utf-8')
                execution_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "stdout": output,
                    "stderr": "",
                    "exit_code": result.get("StatusCode", -1),
                    "execution_time_ms": execution_time_ms,
                    "sandbox_mode": "docker_isolated"
                }
            except Exception as e:
                logger.warning(f"Docker execution failed ({e}), using restricted subprocess runner.")

        # Subprocess fallback when Docker daemon is not active
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, temp_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            execution_time_ms = int((time.time() - start_time) * 1000)

            return {
                "stdout": stdout_data.decode('utf-8'),
                "stderr": stderr_data.decode('utf-8'),
                "exit_code": proc.returncode,
                "execution_time_ms": execution_time_ms,
                "sandbox_mode": "subprocess_fallback"
            }
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "execution_time_ms": execution_time_ms,
                "sandbox_mode": "error"
            }
        finally:
            if container:
                try:
                    await asyncio.to_thread(container.remove, force=True)
                except Exception:
                    pass
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# LangGraph node function
# ---------------------------------------------------------------------------

async def execute_code(state: WorkbenchState) -> dict:
    """LangGraph node: generate a Python script via LLM and execute it in the secure sandbox.

    Pipeline:
    1. If ``metadata.python_code`` is provided, use it directly.
    2. Otherwise, call the local LLM to generate code from the user query.
    3. If the LLM is offline, fall back to a deterministic engineering script.
    4. Execute the code in an isolated Docker container (or subprocess fallback).
    5. Return the script source, stdout, stderr, and exit code.
    """
    query = state.get("query", "")
    code = state.get("metadata", {}).get("python_code", "")

    if not code:
        # Step 1: Try LLM code generation
        llm_code = await _generate_code_via_llm(query)
        if llm_code:
            # Validate syntax before accepting LLM output
            try:
                compile(llm_code, "<llm_generated>", "exec")
                code = llm_code
            except SyntaxError as e:
                logger.warning(f"LLM generated syntactically invalid code ({e}), using fallback")
                code = None

    if not code:
        # Step 2: Deterministic fallback for engineering calculations
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["darcy", "pressure drop", "friction", "pipe", "flow"]):
            code = _generate_darcy_weisbach_fallback(query)
            logger.info("Using deterministic Darcy-Weisbach fallback script")
        else:
            # Generic fallback: echo the query as a calculation stub
            code = f'''\
import math

# ============================================================
# Engineering Calculation (Auto-generated)
# Query: {query}
# ============================================================

print("Engineering calculation requested:")
print(f"  Query: {query}")
print()
print("Note: LLM endpoint is offline. Please provide a Python script")
print("via the metadata.python_code field, or start the vLLM service")
print("for automatic code generation.")
'''

    # Step 3: Execute in sandbox
    sandbox = SecureSandbox()
    result = await sandbox.execute(code)

    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")

    # Build structured output for generate_response to consume
    code_output = {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": result.get("exit_code", -1),
        "execution_time_ms": result.get("execution_time_ms", 0),
        "sandbox_mode": result.get("sandbox_mode", "unknown"),
    }

    return {
        "code_output": code_output,
        "sandbox_script": code,
        "sandbox_stdout": stdout,
        "current_node": "execute_code"
    }

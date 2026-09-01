import docker
import asyncio
import tempfile
import os
import sys
import logging
import time
import subprocess
from agent_core.state import WorkbenchState

logger = logging.getLogger(__name__)

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

async def execute_code(state: WorkbenchState) -> dict:
    """Node function to execute extracted code in the SecureSandbox."""
    code = state.get("metadata", {}).get("python_code", "") or state.get("query", "")
    
    if not code:
        return {
            "error": "No Python code found to execute.",
            "current_node": "execute_code"
        }
        
    sandbox = SecureSandbox()
    result = await sandbox.execute(code)
    
    return {
        "code_output": result,
        "current_node": "execute_code"
    }

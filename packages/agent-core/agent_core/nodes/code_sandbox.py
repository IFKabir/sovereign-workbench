import docker
import asyncio
import tempfile
import os
import logging
import time
from agent_core.state import WorkbenchState

logger = logging.getLogger(__name__)

class SecureSandbox:
    """Provides an isolated Docker environment for executing generated code."""
    def __init__(self, image: str = 'sovereign-sandbox:latest', timeout: int = 30, mem_limit: str = '512m'):
        self.image = image
        self.timeout = timeout
        self.mem_limit = mem_limit
        self.client = docker.from_env()

    async def execute(self, code: str) -> dict:
        """Executes the given Python code in a highly constrained Docker container."""
        container = None
        temp_path = ""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tf:
            tf.write(code)
            temp_path = tf.name
            
        start_time = time.time()
        try:
            # Using asyncio.to_thread to prevent blocking the async event loop with Docker API calls
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
            
            # Wait for container completion with timeout
            def _wait():
                return container.wait(timeout=self.timeout)
            
            result = await asyncio.to_thread(_wait)
            
            # Retrieve logs
            logs = await asyncio.to_thread(container.logs, stdout=True, stderr=True)
            output = logs.decode('utf-8')
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "stdout": output,
                "stderr": "",
                "exit_code": result.get("StatusCode", -1),
                "execution_time_ms": execution_time_ms
            }
            
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "execution_time_ms": execution_time_ms
            }
        finally:
            if container:
                try:
                    await asyncio.to_thread(container.remove, force=True)
                except Exception as cleanup_error:
                    logger.error(f"Failed to remove container: {cleanup_error}")
            
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

async def execute_code(state: WorkbenchState) -> dict:
    """Node function to execute extracted code in the SecureSandbox."""
    # Assuming code is placed in metadata during extraction phase by a prior LLM step
    code = state.get("metadata", {}).get("python_code", "")
    
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

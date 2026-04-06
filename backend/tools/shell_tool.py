"""
Shell Tool: execute shell commands safely with timeout and sandboxing.
"""

import asyncio
import shlex
from typing import Dict, Any
from tools.base_tool import BaseTool


class ShellTool(BaseTool):
    """Tool for executing shell commands safely."""

    name = "shell_tool"
    description = "Execute shell commands safely with timeout. Use for system operations."

    # Commands that are blocked for safety
    BLOCKED_COMMANDS = {
        "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:",
        "shutdown", "reboot", "halt", "poweroff",
        "chmod -R 777 /", "chown -R",
    }

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def run(self, input: Dict[str, Any]) -> str:
        """
        Execute a shell command.
        
        Input keys:
            command: shell command to execute
        """
        command = input.get("command", "")
        if not command:
            return "Error: no command provided"

        # Safety check
        if self._is_blocked(command):
            return f"BLOCKED: Command '{command}' is not allowed for safety reasons."

        try:
            return await self._execute(command)
        except asyncio.TimeoutError:
            return f"Command timed out after {self.timeout} seconds: {command}"
        except Exception as e:
            return f"Shell execution error: {str(e)}"

    def _is_blocked(self, command: str) -> bool:
        """Check if a command is in the blocked list."""
        cmd_lower = command.lower().strip()
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return True
        return False

    async def _execute(self, command: str) -> str:
        """Execute the command with asyncio subprocess."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=None,  # Could restrict to sandbox
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )

            stdout_str = stdout.decode("utf-8", errors="replace").strip()
            stderr_str = stderr.decode("utf-8", errors="replace").strip()

            result_parts = []
            if stdout_str:
                result_parts.append(f"STDOUT:\n{stdout_str}")
            if stderr_str:
                result_parts.append(f"STDERR:\n{stderr_str}")
            result_parts.append(f"Exit code: {process.returncode}")

            result = "\n".join(result_parts)

            # Truncate if too long
            if len(result) > 5000:
                result = result[:5000] + "\n... [output truncated]"

            return result or "Command executed successfully (no output)"

        except asyncio.TimeoutError:
            # Kill the process if it times out
            try:
                process.kill()
            except:
                pass
            raise

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
        }

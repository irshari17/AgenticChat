"""
Shell Tool — safe command execution with timeout and blocklist.
"""

import asyncio
from typing import Dict, Any
from tools.base_tool import BaseTool
import logging

logger = logging.getLogger("tools.shell")


class ShellTool(BaseTool):
    name = "shell_tool"
    description = "Execute shell commands safely with timeout."

    BLOCKED_PATTERNS = [
        "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:",
        "shutdown", "reboot", "halt", "poweroff",
        "chmod -R 777 /", "> /dev/sda",
    ]

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def run(self, input_data: Dict[str, Any]) -> str:
        command = input_data.get("command", "").strip()
        if not command:
            return "Error: no command provided"
        if self._is_blocked(command):
            return "BLOCKED: This command is not allowed for safety reasons."
        try:
            logger.info(f"Executing command: {command}")
            return await self._execute(command)
        except asyncio.TimeoutError:
            return f"Command timed out after {self.timeout}s: {command}"
        except Exception as e:
            return f"Shell error: {str(e)}"

    def _is_blocked(self, command: str) -> bool:
        cmd = command.lower().strip()
        return any(p in cmd for p in self.BLOCKED_PATTERNS)

    async def _execute(self, command: str) -> str:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
            raise

        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()
        parts = []
        if out:
            parts.append(f"STDOUT:\n{out}")
        if err:
            parts.append(f"STDERR:\n{err}")
        parts.append(f"Exit code: {process.returncode}")
        result = "\n".join(parts)
        if len(result) > 5000:
            result = result[:5000] + "\n... [truncated]"
        return result or "Command executed successfully (no output)"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
        }

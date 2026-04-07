"""
File Tool: read and write files safely.
"""

import os
import aiofiles
from typing import Dict, Any
from tools.base_tool import BaseTool


class FileTool(BaseTool):
    name = "file_tool"
    description = "Read or write files. Actions: 'read', 'write', 'list'."

    SANDBOX_DIR = os.path.join(os.getcwd(), "sandbox")

    def __init__(self):
        os.makedirs(self.SANDBOX_DIR, exist_ok=True)

    def _safe_path(self, filepath: str) -> str:
        abs_path = os.path.abspath(os.path.join(self.SANDBOX_DIR, filepath))
        if not abs_path.startswith(os.path.abspath(self.SANDBOX_DIR)):
            raise PermissionError(f"Access denied: path outside sandbox")
        return abs_path

    async def run(self, input: Dict[str, Any]) -> str:
        action = input.get("action", "read")
        path = input.get("path", "")

        try:
            if action == "read":
                return await self._read(path)
            elif action == "write":
                content = input.get("content", "")
                return await self._write(path, content)
            elif action == "list":
                return await self._list(path)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"File tool error: {str(e)}"

    async def _read(self, path: str) -> str:
        safe = self._safe_path(path)
        if not os.path.exists(safe):
            return f"File not found: {path}"
        async with aiofiles.open(safe, "r", encoding="utf-8", errors="replace") as f:
            content = await f.read()
        return f"Contents of {path}:\n{content}"

    async def _write(self, path: str, content: str) -> str:
        safe = self._safe_path(path)
        os.makedirs(os.path.dirname(safe) if os.path.dirname(safe) != safe else safe, exist_ok=True)
        dir_name = os.path.dirname(safe)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        async with aiofiles.open(safe, "w", encoding="utf-8") as f:
            await f.write(content)
        return f"Successfully wrote {len(content)} characters to {path}"

    async def _list(self, path: str = "") -> str:
        safe = self._safe_path(path) if path else self.SANDBOX_DIR
        if not os.path.isdir(safe):
            return f"Not a directory: {path}"
        entries = os.listdir(safe)
        if not entries:
            return f"Directory is empty"
        lines = [f"Contents of {path or '.'}:"]
        for entry in sorted(entries):
            full = os.path.join(safe, entry)
            marker = "📁" if os.path.isdir(full) else "📄"
            lines.append(f"  {marker} {entry}")
        return "\n".join(lines)

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "action": {"type": "string", "enum": ["read", "write", "list"]},
                "path": {"type": "string", "description": "Relative file path"},
                "content": {"type": "string", "description": "Content to write"},
            },
        }

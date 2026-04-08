"""
File Tool — sandboxed file read/write/list operations.
"""

import os
import aiofiles
from typing import Dict, Any
from tools.base_tool import BaseTool
import logging

logger = logging.getLogger("tools.file")


class FileTool(BaseTool):
    name = "file_tool"
    description = "Read, write, or list files. Actions: 'read', 'write', 'list'."

    SANDBOX_DIR = os.path.join(os.getcwd(), "sandbox")

    def __init__(self):
        os.makedirs(self.SANDBOX_DIR, exist_ok=True)

    def _safe_path(self, filepath: str) -> str:
        if not filepath:
            return self.SANDBOX_DIR
        abs_path = os.path.abspath(os.path.join(self.SANDBOX_DIR, filepath))
        if not abs_path.startswith(os.path.abspath(self.SANDBOX_DIR)):
            raise PermissionError("Access denied: path outside sandbox")
        return abs_path

    async def run(self, input_data: Dict[str, Any]) -> str:
        action = input_data.get("action", "read")
        path = input_data.get("path", "")

        try:
            if action == "read":
                return await self._read(path)
            elif action == "write":
                return await self._write(path, input_data.get("content", ""))
            elif action == "list":
                return await self._list(path)
            else:
                return f"Unknown action: {action}. Use: read, write, list"
        except PermissionError as e:
            return f"Permission denied: {e}"
        except Exception as e:
            logger.error(f"File tool error: {e}")
            return f"File tool error: {str(e)}"

    async def _read(self, path: str) -> str:
        safe = self._safe_path(path)
        if not os.path.exists(safe):
            return f"File not found: {path}"
        if os.path.isdir(safe):
            return await self._list(path)
        async with aiofiles.open(safe, "r", encoding="utf-8", errors="replace") as f:
            content = await f.read()
        return f"Contents of '{path}':\n{content}"

    async def _write(self, path: str, content: str) -> str:
        if not path:
            return "Error: no file path specified"
        safe = self._safe_path(path)
        parent = os.path.dirname(safe)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        async with aiofiles.open(safe, "w", encoding="utf-8") as f:
            await f.write(content)
        logger.info(f"File written: {path} ({len(content)} chars)")
        return f"Successfully wrote {len(content)} characters to '{path}'"

    async def _list(self, path: str = "") -> str:
        safe = self._safe_path(path) if path else self.SANDBOX_DIR
        if not os.path.isdir(safe):
            return f"Not a directory: {path}"
        entries = os.listdir(safe)
        if not entries:
            return f"Directory '{path or '.'}' is empty"
        lines = [f"Contents of '{path or '.'}':"]
        for entry in sorted(entries):
            full = os.path.join(safe, entry)
            if os.path.isdir(full):
                lines.append(f"  📁 {entry}/")
            else:
                size = os.path.getsize(full)
                lines.append(f"  📄 {entry} ({size} bytes)")
        return "\n".join(lines)

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "action": {"type": "string", "enum": ["read", "write", "list"], "description": "Operation type"},
                "path": {"type": "string", "description": "Relative file path within sandbox"},
                "content": {"type": "string", "description": "Content to write (for write action)"},
            },
        }

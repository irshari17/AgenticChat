"""
File Tool: read and write files safely.
"""

import os
import aiofiles
from typing import Dict, Any
from tools.base_tool import BaseTool
from core.config import settings


class FileTool(BaseTool):
    """Tool for reading and writing files."""

    name = "file_tool"
    description = "Read or write files on the local filesystem. Actions: 'read', 'write', 'list'."

    # Safety: restrict to a sandbox directory
    SANDBOX_DIR = os.path.join(os.getcwd(), "sandbox")

    def __init__(self):
        os.makedirs(self.SANDBOX_DIR, exist_ok=True)

    def _safe_path(self, filepath: str) -> str:
        """Ensure the path is within the sandbox directory."""
        # Resolve to absolute, prevent directory traversal
        abs_path = os.path.abspath(os.path.join(self.SANDBOX_DIR, filepath))
        if not abs_path.startswith(os.path.abspath(self.SANDBOX_DIR)):
            raise PermissionError(f"Access denied: path outside sandbox: {filepath}")
        return abs_path

    async def run(self, input: Dict[str, Any]) -> str:
        """
        Execute file operation.
        
        Input keys:
            action: "read" | "write" | "list"
            path: relative file path (for read/write)
            content: content to write (for write)
        """
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
                return f"Unknown action: {action}. Supported: read, write, list"
        except PermissionError as e:
            return f"Permission error: {str(e)}"
        except FileNotFoundError:
            return f"File not found: {path}"
        except Exception as e:
            return f"File operation error: {str(e)}"

    async def _read(self, path: str) -> str:
        """Read a file."""
        safe = self._safe_path(path)
        if not os.path.exists(safe):
            return f"File not found: {path}"

        file_size = os.path.getsize(safe)
        if file_size > settings.MAX_FILE_SIZE:
            return f"File too large: {file_size} bytes (max: {settings.MAX_FILE_SIZE})"

        async with aiofiles.open(safe, "r", encoding="utf-8", errors="replace") as f:
            content = await f.read()
        return f"Contents of {path}:\n{content}"

    async def _write(self, path: str, content: str) -> str:
        """Write content to a file."""
        safe = self._safe_path(path)

        # Create directories if needed
        os.makedirs(os.path.dirname(safe), exist_ok=True)

        async with aiofiles.open(safe, "w", encoding="utf-8") as f:
            await f.write(content)
        return f"Successfully wrote {len(content)} characters to {path}"

    async def _list(self, path: str = "") -> str:
        """List directory contents."""
        safe = self._safe_path(path) if path else self.SANDBOX_DIR
        if not os.path.isdir(safe):
            return f"Not a directory: {path}"

        entries = os.listdir(safe)
        if not entries:
            return f"Directory {path or '.'} is empty"

        lines = [f"Contents of {path or '.'}:"]
        for entry in sorted(entries):
            full = os.path.join(safe, entry)
            marker = "📁" if os.path.isdir(full) else "📄"
            size = os.path.getsize(full) if os.path.isfile(full) else ""
            lines.append(f"  {marker} {entry} {f'({size} bytes)' if size else ''}")
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

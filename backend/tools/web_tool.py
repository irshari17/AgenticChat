"""
Web Tool: fetch web data.
"""

import aiohttp
from typing import Dict, Any
from tools.base_tool import BaseTool


class WebTool(BaseTool):
    name = "web_tool"
    description = "Fetch web pages or data from URLs. Actions: 'fetch', 'search_snippet'."

    async def run(self, input: Dict[str, Any]) -> str:
        action = input.get("action", "fetch")
        try:
            if action == "fetch":
                url = input.get("url", "")
                if not url:
                    return "Error: no URL provided"
                return await self._fetch(url)
            elif action == "search_snippet":
                query = input.get("query", "")
                return self._search_snippet(query)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Web tool error: {str(e)}"

    async def _fetch(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={"User-Agent": "AgenticAI/1.0"}) as resp:
                    if resp.status != 200:
                        return f"HTTP {resp.status} error fetching {url}"
                    text = await resp.text()
                    if len(text) > 5000:
                        text = text[:5000] + "\n... [truncated]"
                    return f"Content from {url}:\n{text}"
        except Exception as e:
            return f"Fetch error: {str(e)}"

    def _search_snippet(self, query: str) -> str:
        if not query:
            return "Error: no search query"
        return (
            f"Web search results for '{query}':\n"
            f"(Simulated — integrate with a real search API for production)\n"
            f"1. Relevant info about {query}\n"
            f"2. Additional context for {query}"
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "action": {"type": "string", "enum": ["fetch", "search_snippet"]},
                "url": {"type": "string"},
                "query": {"type": "string"},
            },
        }

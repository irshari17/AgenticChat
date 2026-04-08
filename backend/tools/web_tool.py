"""
Web Tool — fetch web pages and search snippets.
"""

import aiohttp
from typing import Dict, Any
from tools.base_tool import BaseTool
import logging

logger = logging.getLogger("tools.web")


class WebTool(BaseTool):
    name = "web_tool"
    description = "Fetch web pages or search the web. Actions: 'fetch', 'search_snippet'."

    async def run(self, input_data: Dict[str, Any]) -> str:
        action = input_data.get("action", "fetch")
        try:
            if action == "fetch":
                url = input_data.get("url", "")
                if not url:
                    return "Error: no URL provided"
                return await self._fetch(url)
            elif action == "search_snippet":
                query = input_data.get("query", "")
                if not query:
                    return "Error: no query provided"
                return self._search_snippet(query)
            else:
                return f"Unknown action: {action}. Use: fetch, search_snippet"
        except Exception as e:
            logger.error(f"Web tool error: {e}")
            return f"Web tool error: {str(e)}"

    async def _fetch(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        logger.info(f"Fetching URL: {url}")
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={"User-Agent": "AgenticAI/2.0"}) as resp:
                    if resp.status != 200:
                        return f"HTTP {resp.status} error fetching {url}"
                    ct = resp.headers.get("Content-Type", "")
                    if "text" not in ct and "json" not in ct:
                        return f"Non-text content from {url}: {ct}"
                    text = await resp.text()
                    if len(text) > 5000:
                        text = text[:5000] + "\n... [truncated]"
                    return f"Content from {url} (HTTP {resp.status}):\n{text}"
        except aiohttp.ClientError as e:
            return f"Connection error: {str(e)}"

    def _search_snippet(self, query: str) -> str:
        return (
            f"Web search results for '{query}':\n"
            f"(Simulated — integrate with Tavily/SerpAPI for production)\n"
            f"1. Relevant information about {query}\n"
            f"2. Additional context for {query}\n"
            f"3. Related topics for {query}"
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "action": {"type": "string", "enum": ["fetch", "search_snippet"]},
                "url": {"type": "string", "description": "URL to fetch"},
                "query": {"type": "string", "description": "Search query"},
            },
        }

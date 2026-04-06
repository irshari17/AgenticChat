"""
Web Tool: fetch web pages and data from URLs.
"""

import aiohttp
from typing import Dict, Any
from tools.base_tool import BaseTool


class WebTool(BaseTool):
    """Tool for fetching web data."""

    name = "web_tool"
    description = "Fetch web pages or API data from URLs. Actions: 'fetch', 'search_snippet'."

    async def run(self, input: Dict[str, Any]) -> str:
        """
        Execute web operation.
        
        Input keys:
            action: "fetch" | "search_snippet"
            url: URL to fetch (for fetch)
            query: search query (for search_snippet — simulated)
        """
        action = input.get("action", "fetch")

        try:
            if action == "fetch":
                url = input.get("url", "")
                if not url:
                    return "Error: no URL provided"
                return await self._fetch(url)
            elif action == "search_snippet":
                query = input.get("query", "")
                return await self._search_snippet(query)
            else:
                return f"Unknown action: {action}. Supported: fetch, search_snippet"
        except Exception as e:
            return f"Web tool error: {str(e)}"

    async def _fetch(self, url: str) -> str:
        """Fetch content from a URL."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        headers = {
            "User-Agent": "AgenticAI-Bot/1.0 (Learning System)"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    status = resp.status
                    content_type = resp.headers.get("Content-Type", "")

                    if status != 200:
                        return f"HTTP {status} error fetching {url}"

                    if "text" in content_type or "json" in content_type:
                        text = await resp.text()
                        # Truncate very long pages
                        if len(text) > 5000:
                            text = text[:5000] + "\n... [truncated]"
                        return f"Content from {url} (status {status}):\n{text}"
                    else:
                        return f"Non-text content from {url}: {content_type} (status {status})"
        except aiohttp.ClientError as e:
            return f"Connection error: {str(e)}"
        except Exception as e:
            return f"Fetch error: {str(e)}"

    async def _search_snippet(self, query: str) -> str:
        """
        Simulated web search. In production, integrate with a real search API
        (e.g., SerpAPI, Tavily, Brave Search).
        """
        if not query:
            return "Error: no search query provided"

        # Simulated search result for learning/demo purposes
        return (
            f"Web search results for '{query}':\n"
            f"Note: This is a simulated search. In production, connect to a search API.\n"
            f"1. [Simulated] Relevant information about {query}\n"
            f"2. [Simulated] Additional context for {query}\n"
            f"3. [Simulated] Further reading on {query}\n"
            f"\nTo enable real search, integrate with Tavily, SerpAPI, or Brave Search API."
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

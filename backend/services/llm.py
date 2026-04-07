"""
LLM Service: interface to OpenRouter API.
"""

import json
import re
import httpx
from typing import AsyncGenerator, List, Dict, Any, Optional


class LLMService:
    """Service for interacting with OpenRouter LLM API."""

    def __init__(self, api_key: str, base_url: str, model: str):
        if not api_key or not api_key.strip():
            raise ValueError(
                "OPENROUTER_API_KEY is not set. Please set it in backend/.env or via environment variables."
            )
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Agentic AI Chat System",
        }

    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Get a non-streaming completion."""
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            content = data["choices"][0]["message"]["content"]
            return content
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            if e.response.status_code == 401:
                return (
                    f"LLM API error ({e.response.status_code}): {error_body[:500]}"
                    " - check OPENROUTER_API_KEY, account status, and model access"
                )
            return f"LLM API error ({e.response.status_code}): {error_body[:500]}"
        except Exception as e:
            return f"LLM error: {str(e)}"

    async def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Get a streaming completion. Yields text chunks."""
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except Exception as e:
            yield f"\n[Streaming error: {str(e)}]"

    async def complete_json(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """Get a JSON-formatted completion."""
        json_instruction = (
            "\n\nIMPORTANT: Respond ONLY with valid JSON. "
            "No text before or after the JSON. No markdown code fences."
        )

        if system_prompt:
            system_prompt += json_instruction
        else:
            system_prompt = json_instruction

        response_text = await self.complete(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
        )

        return self._extract_json(response_text)

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text."""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code blocks
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in text
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            if start != -1:
                end = text.rfind(end_char)
                if end != -1 and end > start:
                    try:
                        return json.loads(text[start:end + 1])
                    except json.JSONDecodeError:
                        pass

        # Fallback
        return {"raw_response": text, "steps": [], "reasoning": text[:200]}

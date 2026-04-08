"""
LLM Service — OpenRouter API interface with streaming, JSON mode, and retry logic.
"""

import json
import re
import asyncio
import httpx
from typing import AsyncGenerator, List, Dict, Any, Optional
import logging

logger = logging.getLogger("services.llm")


class LLMService:
    def __init__(self, api_key: str, base_url: str, model: str, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_retries = max_retries
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Agentic AI Chat v2",
        }

    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Non-streaming completion with retry logic."""
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                content = data["choices"][0]["message"]["content"]
                logger.debug(f"LLM response ({len(content)} chars)")
                return content

            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:300]}"
                logger.warning(f"LLM attempt {attempt + 1} failed: {last_error}")
                if e.response.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                elif e.response.status_code >= 500:
                    await asyncio.sleep(1)
                else:
                    break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM attempt {attempt + 1} failed: {last_error}")
                await asyncio.sleep(1)

        logger.error(f"LLM failed after {self.max_retries} attempts: {last_error}")
        return f"[LLM Error: {last_error}]"

    async def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming completion."""
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
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data["choices"][0].get("delta", {})
                                chunk = delta.get("content", "")
                                if chunk:
                                    yield chunk
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"\n[Stream error: {str(e)}]"

    async def complete_json(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """Completion that returns parsed JSON."""
        extra = (
            "\n\nCRITICAL: Respond with ONLY valid JSON. "
            "No markdown, no code fences, no extra text. Just the JSON object."
        )
        sp = (system_prompt + extra) if system_prompt else extra
        text = await self.complete(messages=messages, system_prompt=sp, temperature=temperature)
        return self._extract_json(text)

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """Extract JSON from possibly messy LLM output."""
        text = text.strip()

        # Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Code fence extraction
        match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Find JSON object/array
        for sc, ec in [("{", "}"), ("[", "]")]:
            start = text.find(sc)
            if start != -1:
                end = text.rfind(ec)
                if end > start:
                    try:
                        return json.loads(text[start:end + 1])
                    except json.JSONDecodeError:
                        pass

        # Remove thinking tags (Qwen3 sometimes wraps in <think>)
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
        if cleaned != text:
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
            match2 = re.search(r"\{[\s\S]*\}", cleaned)
            if match2:
                try:
                    return json.loads(match2.group(0))
                except json.JSONDecodeError:
                    pass

        logger.warning(f"Could not parse JSON from LLM response: {text[:200]}...")
        return {"raw_response": text, "steps": [], "reasoning": text[:200], "direct_response": None}

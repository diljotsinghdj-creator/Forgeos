"""OpenAI-compatible chat endpoint: Ollama (/v1), llama.cpp server, vLLM, LM Studio, or any
hosted API you choose to point at. No vendor is required."""
from __future__ import annotations

import httpx

from .base import ProviderError


class OpenAICompatibleLLM:
    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: float = 600):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.id = f"llm:{model}"

    def complete_json(self, system: str, user: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = {
            "model": self.model,
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        try:
            r = httpx.post(f"{self.base_url}/chat/completions", json=body, headers=headers, timeout=self.timeout)
        except httpx.HTTPError as e:
            raise ProviderError(f"LLM unreachable at {self.base_url}: {e}") from e
        if r.status_code >= 400:
            raise ProviderError(f"LLM HTTP {r.status_code}: {r.text[:300]}")
        try:
            return r.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise ProviderError(f"LLM returned an unexpected response: {r.text[:300]}") from e

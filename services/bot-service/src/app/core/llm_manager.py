import asyncio
import logging
import random
from typing import Any, Dict, List, Optional

import httpx

from .config import settings

logger = logging.getLogger("bot-service.llm")


class LLMError(RuntimeError):
    pass


class AsyncLLMManager:
    """
    Async LLM manager with typed signatures to satisfy static analysis.
    """

    def __init__(self, orchestrator_client: Any, http_client: Optional[httpx.AsyncClient] = None) -> None:
        self.orchestrator = orchestrator_client
        self._client_owned = False
        if http_client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
            self._client_owned = True
        else:
            self._client = http_client

        # config
        self.default_model: str = str(getattr(settings, "DEFAULT_MODEL", "gemini"))

        self.gemini_key: Optional[str] = getattr(settings, "GEMINI_API_KEY", None)
        self.gemini_api_url: str = str(
            getattr(
                settings,
                "GEMINI_API_URL",
                "https://generativelanguage.googleapis.com/v1beta2/models/{model}:generateText",
            )
        )
        self.gemini_timeout_ms: int = int(getattr(settings, "GEMINI_TIMEOUT_MS", 30000))
        self.gemini_retries: int = int(getattr(settings, "GEMINI_RETRIES", 3))

        self.groq_key: Optional[str] = getattr(settings, "GROQ_API_KEY", None)
        self.groq_api_url: Optional[str] = getattr(settings, "GROQ_API_URL", None)
        self.groq_timeout_ms: int = int(getattr(settings, "GROQ_TIMEOUT_MS", 20000))
        self.groq_retries: int = int(getattr(settings, "GROQ_RETRIES", 2))

    async def close(self) -> None:
        if self._client_owned:

    async def get_model_service(self, model: Optional[str] = None):
        """
        Return a synchronous model service instance matching the requested model.
        The Orchestrator expects a service with a blocking `invoke(prompt)` method
        so we return the appropriate BaseModelService implementation.
        """
        # Local imports to avoid circular import at module import time
        try:
            from ..services.gemini_service import GeminiService
            from ..services.groq_service import GroqService
        except Exception:
            # If services are not importable, raise a clear error
            raise LLMError("model service implementations unavailable")

        provider = (model or self.default_model or "gemini").lower()
        if provider.startswith("groq"):
            return GroqService(self.groq_key)
        return GeminiService(self.gemini_key)
            await self._client.aclose()

    async def generate_chat(
        self, message: str, system_prompt: Optional[str] = None, model: Optional[str] = None, max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        provider = (model or self.default_model or "gemini").lower()
        if provider.startswith("groq"):
            return await self._generate_groq(message, system_prompt, model)
        return await self._generate_gemini(message, system_prompt, model)

    async def _request_with_retries(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json: Dict[str, Any],
        timeout_ms: int,
        retries: int,
    ) -> httpx.Response:
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= retries:
            try:
                timeout = httpx.Timeout(timeout_ms / 1000.0)
                resp = await self._client.request(method, url, headers=headers, json=json, timeout=timeout)
                if 500 <= resp.status_code < 600:
                    raise httpx.HTTPStatusError("server error", request=resp.request, response=resp)
                return resp
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                backoff = min(2 ** attempt, 10)
                jitter = random.uniform(0, 0.5)
                wait = backoff + jitter
                logger.warning("LLM request attempt %d failed: %s — retrying in %.2fs", attempt + 1, str(exc), wait)
                await asyncio.sleep(wait)
                attempt += 1
        logger.error("LLM request failed after %d attempts: %s", retries + 1, repr(last_exc))
        raise LLMError("provider request failed") from last_exc

    async def _generate_groq(self, message: str, system_prompt: Optional[str], model: Optional[str]) -> Dict[str, Any]:
        if not self.groq_api_url:
            raise LLMError("GROQ_API_URL not configured")
        if not self.groq_key:
            raise LLMError("GROQ_API_KEY not configured")

        url = self.groq_api_url
        headers: Dict[str, str] = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        payload: Dict[str, Any] = {"model": model or "groq-1", "messages": messages}

        resp = await self._request_with_retries("POST", url, headers, payload, timeout_ms=self.groq_timeout_ms, retries=self.groq_retries)
        try:
            data: Any = resp.json()
        except Exception as e:
            logger.exception("Failed parsing GROQ response JSON")
            raise LLMError("invalid provider response") from e

        text: Optional[str] = None
        if isinstance(data, dict):
            if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                choice: Any = data["choices"][0]
                if isinstance(choice, dict):
                    msg = choice.get("message") if isinstance(choice.get("message"), dict) else None
                    if msg:
                        text = msg.get("content") or msg.get("text")
                    else:
                        text = choice.get("text") or choice.get("message")
            text = text or data.get("text") or data.get("response")

        if not text:
            logger.error("GROQ provider returned unexpected payload: status=%s keys=%s", resp.status_code, list(data.keys()) if isinstance(data, dict) else None)
            raise LLMError("provider returned no text")

        return {"response_message": str(text), "provider": "groq", "raw": data}

    async def _generate_gemini(self, message: str, system_prompt: Optional[str], model: Optional[str]) -> Dict[str, Any]:
        if not self.gemini_key:
            raise LLMError("GEMINI_API_KEY not configured")

        model_name = model or self.default_model
        api_template = self.gemini_api_url
        if "{model}" in api_template:
            url = api_template.format(model=model_name)
            if "generativelanguage.googleapis.com" in url and "?" not in url:
                url = f"{url}?key={self.gemini_key}"
        else:
            url = api_template

        headers: Dict[str, str] = {}
        if api_template and "bearer" in api_template.lower():
            headers["Authorization"] = f"Bearer {self.gemini_key}"
        headers["Content-Type"] = "application/json"

        payload: Dict[str, Any] = {"prompt": {"text": message}}
        if system_prompt:
            payload["prompt"]["prefix"] = system_prompt

        resp = await self._request_with_retries("POST", url, headers, payload, timeout_ms=self.gemini_timeout_ms, retries=self.gemini_retries)
        try:
            data: Any = resp.json()
        except Exception as e:
            logger.exception("Failed parsing Gemini response JSON")
            raise LLMError("invalid provider response") from e

        text: Optional[str] = None
        if isinstance(data, dict):
            if "candidates" in data and isinstance(data["candidates"], list) and data["candidates"]:
                cand: Any = data["candidates"][0]
                if isinstance(cand, dict):
                    text = cand.get("content") or cand.get("output") or cand.get("html")
            text = text or data.get("output") or data.get("text") or data.get("content")

        if not text:
            logger.error("Gemini provider returned unexpected payload: status=%s keys=%s", resp.status_code, list(data.keys()) if isinstance(data, dict) else None)
            raise LLMError("provider returned no text")

        return {"response_message": str(text), "provider": "gemini", "raw": data}

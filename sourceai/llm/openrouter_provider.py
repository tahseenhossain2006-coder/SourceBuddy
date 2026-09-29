# sourceai/llm/openrouter_provider.py
import json
import time
import logging
from typing import List, Dict, Any, Optional
import requests
from .provider import LLMProvider

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "SourceAI/1.0"


class OpenRouterProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str],
        base_url: str,
        default_model: str,
        reasoning_enabled: bool = True,
        default_timeout: int = 60,
        http_referer: Optional[str] = None,
        x_title: Optional[str] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.reasoning_enabled = reasoning_enabled
        self.default_timeout = default_timeout
        self.http_referer = http_referer
        self.x_title = x_title

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        })
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
        if self.http_referer:
            self.session.headers["HTTP-Referer"] = self.http_referer
        if self.x_title:
            self.session.headers["X-Title"] = self.x_title

        self.session.trust_env = False

    def list_models(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/models"
        try:
            resp = self.session.get(url, timeout=self.default_timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"OpenRouter list_models failed: {e}")
            return []

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        response_format: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if self.reasoning_enabled and model.startswith("nvidia/nemotron"):
            payload["reasoning"] = {"enabled": True}

        # response_format is not supported by nemotron-3.5-lightning:free
        if response_format and not model.startswith("nvidia/nemotron-3.5-lightning"):
            payload["response_format"] = response_format

        timeout = timeout_seconds or self.default_timeout
        try:
            resp = self.session.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            if content is None:
                raise RuntimeError("OpenRouter returned empty content")
            return content
        except requests.exceptions.Timeout:
            raise RuntimeError(f"OpenRouter timeout after {timeout}s")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise RuntimeError("OpenRouter authentication failed")
            elif e.response.status_code == 429:
                raise RuntimeError("OpenRouter rate limit exceeded")
            elif 500 <= e.response.status_code < 600:
                raise RuntimeError(f"OpenRouter upstream error: {e.response.status_code}")
            else:
                raise RuntimeError(f"OpenRouter error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"OpenRouter request failed: {e}")

    def health_check(self, model: Optional[str] = None) -> Dict[str, Any]:
        start = time.perf_counter()
        test_model = model or "nvidia/nemotron-3.5-lightning:free"
        try:
            result = self.generate(
                messages=[{"role": "user", "content": "Reply with exactly: SOURCEAI_OPENROUTER_OK"}],
                model=test_model,
                max_tokens=20,
                temperature=0.0,
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {
                "connected": True,
                "provider": "openrouter",
                "model": test_model,
                "latency_ms": latency_ms,
                "real_inference": True,
                "response": result,
            }
        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {
                "connected": False,
                "provider": "openrouter",
                "model": test_model,
                "latency_ms": latency_ms,
                "real_inference": False,
                "error": str(e),
            }
# sourceai/llm/ollama_provider.py
import json
import logging
import time
import requests
from typing import List, Dict, Any, Optional
from .provider import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Provider adapter for local Ollama (OpenAI-compatible API at /v1).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_timeout: int = 60,
        default_model: str = "llama3.2:3b",
    ):
        # Ollama exposes both /api/* (native) and /v1/* (OpenAI-compatible).
        # We use /v1 for consistency with the rest of the codebase.
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/v1"):
            self.base_url = self.base_url + "/v1"
        self.default_timeout = default_timeout
        self.default_model = default_model

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.trust_env = False

    # ------------------------------------------------------------------
    # list_models
    # ------------------------------------------------------------------
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List locally installed Ollama models.
        Ollama's OpenAI-compatible endpoint may not always expose /v1/models,
        so we fall back to the native /api/tags endpoint.
        """
        # Try OpenAI-compatible endpoint first
        try:
            r = self.session.get(f"{self.base_url}/models", timeout=self.default_timeout)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
        except Exception:
            pass

        # Fall back to native Ollama endpoint
        native = self.base_url.replace("/v1", "")
        try:
            r = self.session.get(f"{native}/api/tags", timeout=self.default_timeout)
            r.raise_for_status()
            data = r.json()
            models = data.get("models", [])
            return [
                {
                    "id": m.get("name") or m.get("model"),
                    "object": "model",
                    "owned_by": "ollama",
                }
                for m in models
            ]
        except Exception as e:
            logger.warning(f"Ollama list_models failed: {e}")
            return []

    # ------------------------------------------------------------------
    # generate
    # ------------------------------------------------------------------
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
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        timeout = timeout_seconds or self.default_timeout
        try:
            r = self.session.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if content is None:
                raise RuntimeError("Ollama returned no content")
            return content
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Ollama timeout after {timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"Ollama not reachable at {self.base_url}. Is it running? ({e})"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama request failed: {e}")

    # ------------------------------------------------------------------
    # health_check
    # ------------------------------------------------------------------
    def health_check(self, model: Optional[str] = None) -> Dict[str, Any]:
        start = time.perf_counter()
        test_model = model or self.default_model
        try:
            result = self.generate(
                messages=[
                    {"role": "user", "content": "Reply with exactly: SOURCEAI_HEALTH_OK"}
                ],
                model=test_model,
                max_tokens=20,
                temperature=0.0,
                timeout_seconds=60,
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {
                "connected": True,
                "provider": "ollama",
                "model": test_model,
                "latency_ms": latency_ms,
                "real_inference": True,
                "response": result,
            }
        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {
                "connected": False,
                "provider": "ollama",
                "model": test_model,
                "latency_ms": latency_ms,
                "real_inference": False,
                "error": str(e),
            }
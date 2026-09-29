import time
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .provider import LLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None, default_timeout: int = 30):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.default_timeout = default_timeout

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        response_format: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                timeout=timeout_seconds or self.default_timeout,
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response")
            return content
        except Exception as e:
            raise RuntimeError(f"OpenAI request failed: {e}")

    def health_check(self, model: Optional[str] = None) -> Dict[str, Any]:
        start = time.time()
        try:
            _ = self.generate(
                messages=[{"role": "user", "content": "Say 'OK'"}],
                model=model or "gpt-3.5-turbo",
                max_tokens=10,
                temperature=0.0
            )
            latency_ms = int((time.time() - start) * 1000)
            return {
                "connected": True,
                "provider": "openai",
                "model": model or "gpt-3.5-turbo",
                "latency_ms": latency_ms,
                "real_inference": True
            }
        except Exception as e:
            return {
                "connected": False,
                "provider": "openai",
                "model": model or "gpt-3.5-turbo",
                "error": str(e),
                "real_inference": False
            }
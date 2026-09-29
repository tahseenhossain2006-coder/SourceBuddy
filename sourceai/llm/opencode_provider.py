import json
import time
import logging
from urllib import request, error
from typing import List, Dict, Any, Optional
from .provider import LLMProvider

logger = logging.getLogger(__name__)

class OpenCodeProvider(LLMProvider):
    def __init__(self, api_key: Optional[str], base_url: str, default_timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_timeout = default_timeout

    def list_models(self) -> List[Dict[str, Any]]:
        """Retrieve model list from OpenCode API."""
        url = f"{self.base_url}/models"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = request.Request(url, headers=headers)
        try:
            with request.urlopen(req, timeout=self.default_timeout) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data.get("data", [])
        except Exception as e:
            logger.warning(f"OpenCode list_models failed: {e}")
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
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        data = json.dumps(payload).encode('utf-8')
        req = request.Request(url, data=data, headers=headers, method='POST')
        timeout = timeout_seconds or self.default_timeout
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                response_data = json.loads(resp.read().decode('utf-8'))
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    raise ValueError("Empty response")
                return content
        except error.HTTPError as e:
            try:
                error_body = e.read().decode('utf-8')
                error_json = json.loads(error_body)
                error_msg = error_json.get("error", {}).get("message", str(e))
            except:
                error_msg = str(e)
            raise RuntimeError(f"HTTP error {e.code}: {error_msg}")
        except error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}")

    def health_check(self, model: Optional[str] = None) -> Dict[str, Any]:
        start = time.time()
        try:
            _ = self.generate(
                messages=[{"role": "user", "content": "Reply with exactly: SOURCEAI_HEALTH_OK"}],
                model=model or self.list_models()[0].get("id") if self.list_models() else "oc/big-pickle",
                max_tokens=20,
                temperature=0.0
            )
            latency_ms = int((time.time() - start) * 1000)
            return {
                "connected": True,
                "provider": "opencode",
                "model": model or "opencode/default",
                "latency_ms": latency_ms,
                "real_inference": True
            }
        except Exception as e:
            return {
                "connected": False,
                "provider": "opencode",
                "model": model or "opencode/default",
                "error": str(e),
                "real_inference": False
            }
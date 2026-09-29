from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    Groq,
)

from .provider import LLMProvider

logger = logging.getLogger(__name__)

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
FALLBACK_GROQ_MODEL = "openai/gpt-oss-20b"

SUPPORTED_GROQ_MODELS = {
    DEFAULT_GROQ_MODEL,
    FALLBACK_GROQ_MODEL,
}

# GPT-OSS models are reasoning models: they spend tokens on internal
# reasoning before any final content is emitted. If max_completion_tokens
# is too small, the model can exhaust the budget on reasoning alone and
# return finish_reason=length with empty content. This floor gives the
# model enough room to produce an answer even when the caller asks for
# a very small completion.
MIN_REASONING_TOKENS = 1024


def _normalize_groq_base_url(url: Optional[str]) -> str:
    """
    Groq SDK appends `/openai/v1` internally. If the caller passes a base URL
    that already contains that path (common when reusing a shared
    OpenAI-compatible config such as settings.GROQ_BASE_URL), the request URL
    ends up doubled:
        POST /openai/v1/openai/v1/chat/completions  -> 404
    Strip the trailing path so the SDK produces the correct URL.
    """
    normalized = (url or "https://api.groq.com").rstrip("/")
    if normalized.endswith("/openai/v1"):
        normalized = normalized[: -len("/openai/v1")]
    return normalized or "https://api.groq.com"


class GroqProvider(LLMProvider):
    """
    Groq provider using the official Groq Python SDK.

    SourceAI policy:
    - Primary: GPT-OSS 120B
    - Model fallback: GPT-OSS 20B
    - No Qwen
    - Reasoning hidden by default
    - Structured-output compatible
    - Provider errors are classified for the higher-level router
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.groq.com",
        default_timeout: float = 60.0,
        default_model: str = DEFAULT_GROQ_MODEL,
        fallback_models: Optional[List[str]] = None,
    ):
        self.api_key = api_key
        self.base_url = _normalize_groq_base_url(base_url)
        self.default_timeout = default_timeout
        self.default_model = default_model

        self.fallback_models = fallback_models or [
            FALLBACK_GROQ_MODEL,
        ]

        self.client: Optional[Groq] = None

        if self.api_key:
            self.client = Groq(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.default_timeout,
            )

    # ------------------------------------------------------------------
    # Provider metadata
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return bool(self.api_key and self.client)

    def supports_model(self, model_id: str) -> bool:
        return model_id in SUPPORTED_GROQ_MODELS

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    def list_models(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []

        try:
            response = self.client.models.list()

            models: List[Dict[str, Any]] = []

            for model in response.data:
                models.append(
                    {
                        "id": getattr(model, "id", None),
                        "object": getattr(model, "object", None),
                        "created": getattr(model, "created", None),
                        "owned_by": getattr(model, "owned_by", None),
                    }
                )

            return models

        except APIStatusError as exc:
            raise RuntimeError(
                self._format_api_error(
                    exc,
                    operation="model listing",
                )
            ) from exc

        except APIConnectionError as exc:
            raise RuntimeError(
                f"Groq connection failed while listing models: {exc}"
            ) from exc

        except APITimeoutError as exc:
            raise RuntimeError(
                f"Groq model listing timed out after "
                f"{self.default_timeout}s"
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected Groq model-listing error")
            raise RuntimeError(
                f"Groq model listing failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Error classification
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_status(status_code: Optional[int]) -> str:
        if status_code == 400:
            return "bad_request"

        if status_code == 401:
            return "authentication"

        if status_code == 403:
            return "permission"

        if status_code == 404:
            return "model_not_found"

        if status_code == 408:
            return "timeout"

        if status_code == 409:
            return "conflict"

        if status_code == 413:
            return "context_too_large"

        if status_code == 429:
            return "rate_limit"

        if status_code is not None and status_code >= 500:
            return "server_error"

        return "api_error"

    @staticmethod
    def _format_api_error(
        exc: APIStatusError,
        operation: str = "request",
    ) -> str:
        status_code = getattr(exc, "status_code", None)
        category = GroqProvider._classify_status(status_code)

        return (
            f"Groq {operation} failed: "
            f"category={category}, "
            f"status={status_code}, "
            f"error={exc}"
        )

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        if not self.client:
            raise RuntimeError(
                "Groq provider is not configured"
            )

        selected_model = model or self.default_model

        if not self.supports_model(selected_model):
            raise ValueError(
                f"Unsupported Groq model: {selected_model}"
            )

        # --------------------------------------------------------------
        # GPT-OSS uses max_completion_tokens. Keep max_tokens in our
        # SourceAI interface for compatibility, but translate it to
        # Groq's current parameter.
        #
        # Reasoning models need a floor: they can burn the entire budget
        # on internal reasoning and return finish_reason=length with
        # empty content. Apply the floor here so callers can ask for a
        # small answer without the request failing.
        # --------------------------------------------------------------

        effective_max_tokens = max(max_tokens, MIN_REASONING_TOKENS)

        payload: Dict[str, Any] = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": effective_max_tokens,
            "include_reasoning": False,
            "reasoning_effort": "low",
        }

        # --------------------------------------------------------------
        # Structured output
        # --------------------------------------------------------------

        if response_format is not None:
            payload["response_format"] = response_format

        # --------------------------------------------------------------
        # Optional parameters
        # --------------------------------------------------------------

        allowed_kwargs = {
            "top_p",
            "stop",
            "seed",
            "reasoning_effort",
            "include_reasoning",
            "tools",
            "tool_choice",
            "parallel_tool_calls",
        }

        for key in allowed_kwargs:
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]

        start = time.perf_counter()

        try:
            response = self.client.chat.completions.create(
                **payload
            )

            latency_ms = int(
                (time.perf_counter() - start) * 1000
            )

            # ----------------------------------------------------------
            # Validate choices
            # ----------------------------------------------------------

            if not response.choices:
                raise RuntimeError(
                    "Groq returned no choices"
                )

            choice = response.choices[0]
            message = choice.message

            # ----------------------------------------------------------
            # GPT-OSS final answer
            # ----------------------------------------------------------

            content = getattr(
                message,
                "content",
                None,
            ) or ""

            # Reasoning is deliberately not exposed by default.
            reasoning = getattr(
                message,
                "reasoning",
                None,
            )

            # ----------------------------------------------------------
            # A response with no final content is a real failure for
            # SourceAI, even if the HTTP request succeeded.
            # ----------------------------------------------------------

            if not content.strip():
                finish_reason = getattr(
                    choice,
                    "finish_reason",
                    None,
                )

                raise RuntimeError(
                    "Groq returned an empty final response "
                    f"(finish_reason={finish_reason})"
                )

            # ----------------------------------------------------------
            # Usage
            # ----------------------------------------------------------

            usage = getattr(
                response,
                "usage",
                None,
            )

            usage_data: Optional[Dict[str, Any]] = None

            if usage is not None:
                usage_data = {
                    "prompt_tokens": getattr(
                        usage,
                        "prompt_tokens",
                        None,
                    ),
                    "completion_tokens": getattr(
                        usage,
                        "completion_tokens",
                        None,
                    ),
                    "total_tokens": getattr(
                        usage,
                        "total_tokens",
                        None,
                    ),
                }

            # ----------------------------------------------------------
            # Return normalized SourceAI result
            # ----------------------------------------------------------

            return {
                "content": content,
                "model": getattr(
                    response,
                    "model",
                    selected_model,
                ),
                "provider": "groq",
                "latency_ms": latency_ms,
                "finish_reason": getattr(
                    choice,
                    "finish_reason",
                    None,
                ),
                "usage": usage_data,
                "reasoning": reasoning,
                "raw_response": response,
            }

        except APITimeoutError as exc:
            raise RuntimeError(
                "Groq request timed out "
                f"after {self.default_timeout}s"
            ) from exc

        except APIConnectionError as exc:
            raise RuntimeError(
                f"Groq connection failed: {exc}"
            ) from exc

        except APIStatusError as exc:
            raise RuntimeError(
                self._format_api_error(exc)
            ) from exc

        except RuntimeError:
            # Preserve our intentional SourceAI errors.
            raise

        except Exception as exc:
            logger.exception(
                "Unexpected Groq generation error"
            )

            raise RuntimeError(
                f"Groq request failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        if not self.is_available():
            return {
                "connected": False,
                "provider": "groq",
                "model": self.default_model,
                "real_inference": False,
                "error": (
                    "Groq provider is not configured"
                ),
            }

        start = time.perf_counter()

        try:
            result = self.generate(
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Reply with exactly: "
                            "SOURCEAI_GROQ_OK"
                        ),
                    }
                ],
                model=self.default_model,
                temperature=0.0,
                max_tokens=128,
                include_reasoning=False,
                reasoning_effort="low",
            )

            latency_ms = int(
                (time.perf_counter() - start) * 1000
            )

            return {
                "connected": True,
                "provider": "groq",
                "model": result["model"],
                "latency_ms": latency_ms,
                "real_inference": True,
                "response": result["content"],
                "finish_reason": result.get(
                    "finish_reason"
                ),
                "usage": result.get("usage"),
            }

        except Exception as exc:
            latency_ms = int(
                (time.perf_counter() - start) * 1000
            )

            return {
                "connected": False,
                "provider": "groq",
                "model": self.default_model,
                "latency_ms": latency_ms,
                "real_inference": False,
                "error": str(exc),
            }
# sourceai/llm/router.py

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .config import LLMConfig
from .model_registry import (
    ModelCapability,
    ModelDefinition,
    ModelHealthStatus,
    ModelRegistry,
)
from .provider import LLMProvider
from .tasks import LLMTask, TASK_CAPABILITY_MAP

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Routing errors
# ---------------------------------------------------------------------------

class RoutingError(RuntimeError):
    """Base error raised by the SourceAI model router."""


class PermanentModelError(RoutingError):
    """The selected provider/model cannot currently perform the request."""


class RateLimitError(RoutingError):
    """Provider/model rate limit was reached."""


class TemporaryProviderError(RoutingError):
    """Transient provider/network/server failure."""


class ContextTooLargeError(RoutingError):
    """Request is too large for the selected model/provider."""


# ---------------------------------------------------------------------------
# Route context
# ---------------------------------------------------------------------------

@dataclass
class RouteContext:
    """
    State carried through model/provider fallback.

    The important property is that fallback does NOT recreate the task.
    The same messages and accumulated state can continue with another model.
    """

    task: str
    messages: List[Dict[str, Any]]

    current_step: Optional[str] = None

    completed_steps: List[str] = field(default_factory=list)
    remaining_steps: List[str] = field(default_factory=list)

    previous_output: Optional[str] = None
    last_provider: Optional[str] = None
    last_model: Optional[str] = None

    attempts: int = 0
    failures: List[Dict[str, Any]] = field(default_factory=list)

    def checkpoint(self) -> Dict[str, Any]:
        """Return serializable routing state."""
        return {
            "task": self.task,
            "messages": self.messages,
            "current_step": self.current_step,
            "completed_steps": list(self.completed_steps),
            "remaining_steps": list(self.remaining_steps),
            "previous_output": self.previous_output,
            "last_provider": self.last_provider,
            "last_model": self.last_model,
            "attempts": self.attempts,
            "failures": list(self.failures),
        }


# ---------------------------------------------------------------------------
# Model router
# ---------------------------------------------------------------------------

class ModelRouter:
    """
    Central SourceAI LLM router.

    Provider/model priority:

        Groq GPT-OSS 120B
            ↓
        Groq GPT-OSS 20B
            ↓
        OpenRouter configured model
            ↓
        OmniRoute configured model

    No Qwen models are registered or selected here.
    """

    def __init__(
        self,
        config: LLMConfig,
        providers: Dict[str, LLMProvider],
    ):
        self.config = config
        self.providers = providers

        self.registry = ModelRegistry()

        # Do NOT perform expensive real inference probes during construction.
        self._register_models_from_config()

    # ------------------------------------------------------------------
    # Registry setup
    # ------------------------------------------------------------------

    def _register_models_from_config(self) -> None:
        """
        Register only the models SourceAI intentionally supports.

        Provider discovery must not silently introduce arbitrary models such
        as Qwen into the production routing chain.
        """

        # --------------------------------------------------------------
        # Groq
        # --------------------------------------------------------------

        groq_models = self.config.get_groq_models()

        for index, model_id in enumerate(groq_models):
            if index == 0:
                display_name = "Groq GPT-OSS 120B"
                priority = 100
            else:
                display_name = "Groq GPT-OSS 20B"
                priority = 90

            self._register_if_missing(
                ModelDefinition(
                    model_id=model_id,
                    provider="groq",
                    display_name=display_name,
                    capabilities=[
                        ModelCapability.FAST,
                        ModelCapability.GENERAL,
                        ModelCapability.REASONING,
                        ModelCapability.EXTRACTION,
                    ],
                    task_categories=[],
                    priority=priority,
                    supports_reasoning=True,
                    enabled=True,
                    health_status=ModelHealthStatus.UNKNOWN,
                    timeout=self.config.timeout_seconds,
                    max_tokens=4096,
                )
            )

        # --------------------------------------------------------------
        # OpenRouter
        # --------------------------------------------------------------

        if self.config.openrouter_default_model:
            self._register_if_missing(
                ModelDefinition(
                    model_id=self.config.openrouter_default_model,
                    provider="openrouter",
                    display_name="OpenRouter Fallback",
                    capabilities=[
                        ModelCapability.FAST,
                        ModelCapability.GENERAL,
                        ModelCapability.REASONING,
                        ModelCapability.EXTRACTION,
                    ],
                    task_categories=[],
                    priority=80,
                    supports_reasoning=self.config.openrouter_reasoning_enabled,
                    enabled=True,
                    health_status=ModelHealthStatus.UNKNOWN,
                    timeout=self.config.timeout_seconds,
                    max_tokens=4096,
                )
            )

        # --------------------------------------------------------------
        # OmniRoute
        # --------------------------------------------------------------

        if self.config.omniroute_default_model:
            self._register_if_missing(
                ModelDefinition(
                    model_id=self.config.omniroute_default_model,
                    provider="omniroute",
                    display_name="OmniRoute Fallback",
                    capabilities=[
                        ModelCapability.FAST,
                        ModelCapability.GENERAL,
                        ModelCapability.REASONING,
                        ModelCapability.EXTRACTION,
                    ],
                    task_categories=[],
                    priority=70,
                    supports_reasoning=True,
                    enabled=True,
                    health_status=ModelHealthStatus.UNKNOWN,
                    timeout=self.config.timeout_seconds,
                    max_tokens=4096,
                )
            )

        # --------------------------------------------------------------
        # Prompt Guard
        # --------------------------------------------------------------

        self._register_if_missing(
            ModelDefinition(
                model_id="meta-llama/llama-prompt-guard-2-86m",
                provider="groq",
                display_name="Prompt Guard 86M",
                capabilities=[ModelCapability.SECURITY],
                task_categories=[LLMTask.PROMPT_INJECTION_DETECTION.value],
                priority=100,
                supports_reasoning=False,
                security_role="prompt_guard",
                enabled=True,
                health_status=ModelHealthStatus.UNKNOWN,
                timeout=self.config.timeout_seconds,
                max_tokens=512,
            )
        )

        self._register_if_missing(
            ModelDefinition(
                model_id="meta-llama/llama-prompt-guard-2-22m",
                provider="groq",
                display_name="Prompt Guard 22M",
                capabilities=[ModelCapability.SECURITY],
                task_categories=[LLMTask.PROMPT_INJECTION_DETECTION.value],
                priority=90,
                supports_reasoning=False,
                security_role="prompt_guard",
                enabled=True,
                health_status=ModelHealthStatus.UNKNOWN,
                timeout=self.config.timeout_seconds,
                max_tokens=512,
            )
        )

    def _register_if_missing(self, model: ModelDefinition) -> None:
        existing = self.registry.get(model.model_id)

        if existing is None:
            self.registry.register(model)
            return

        # Keep runtime health information while refreshing configuration.
        existing.provider = model.provider
        existing.display_name = model.display_name
        existing.capabilities = model.capabilities
        existing.priority = model.priority
        existing.supports_reasoning = model.supports_reasoning
        existing.security_role = model.security_role
        existing.enabled = model.enabled
        existing.timeout = model.timeout
        existing.max_tokens = model.max_tokens

    # ------------------------------------------------------------------
    # Task handling
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_task(task: str | LLMTask) -> LLMTask:
        if isinstance(task, LLMTask):
            return task

        try:
            return LLMTask(str(task))
        except ValueError:
            logger.warning(
                "Unknown LLM task '%s'; using final_answer capability.",
                task,
            )
            return LLMTask.FINAL_ANSWER

    @staticmethod
    def _capability_for_task(task: LLMTask) -> str:
        return TASK_CAPABILITY_MAP.get(
            task,
            "reasoning",
        )

    @staticmethod
    def _capability_enum(capability: str) -> Optional[ModelCapability]:
        try:
            return ModelCapability(capability)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Candidate selection
    # ------------------------------------------------------------------

    def _candidate_models(
        self,
        task: LLMTask,
    ) -> List[ModelDefinition]:

        capability_name = self._capability_for_task(task)
        capability = self._capability_enum(capability_name)

        if capability is None:
            return []

        models = self.registry.get_capability_models(capability)

        # Explicit provider order from config is authoritative.
        provider_rank = {
            provider.lower(): index
            for index, provider in enumerate(self.config.provider_order)
        }

        def sort_key(model: ModelDefinition):
            return (
                provider_rank.get(model.provider.lower(), 999),
                -model.priority,
            )

        models.sort(key=sort_key)

        # Security tasks should ONLY use security models.
        if capability == ModelCapability.SECURITY:
            models = [
                model
                for model in models
                if model.security_role == "prompt_guard"
            ]

        return models

    # ------------------------------------------------------------------
    # Provider availability
    # ------------------------------------------------------------------

    def _provider_available(self, provider: LLMProvider) -> bool:
        try:
            return bool(provider.is_available())
        except Exception as exc:
            logger.warning(
                "Provider availability check failed: %s",
                exc,
            )
            return False

    # ------------------------------------------------------------------
    # Error classification
    # ------------------------------------------------------------------

    @staticmethod
    def _status_code_from_error(error: Exception) -> Optional[int]:
        for attribute in (
            "status_code",
            "status",
            "http_status",
        ):
            value = getattr(error, attribute, None)

            if isinstance(value, int):
                return value

        response = getattr(error, "response", None)

        if response is not None:
            value = getattr(response, "status_code", None)

            if isinstance(value, int):
                return value

        return None

    @classmethod
    def _classify_error(cls, error: Exception) -> str:
        status = cls._status_code_from_error(error)

        message = str(error).lower()

        if status in {401, 403, 404}:
            return "permanent"

        if status == 413:
            return "context"

        if status == 429:
            return "rate_limit"

        if status in {408, 409}:
            return "temporary"

        if status is not None and status >= 500:
            return "temporary"

        if any(
            token in message
            for token in (
                "rate limit",
                "ratelimit",
                "too many requests",
                "quota",
                "resource exhausted",
            )
        ):
            return "rate_limit"

        if any(
            token in message
            for token in (
                "context length",
                "context window",
                "maximum context",
                "too large",
                "payload too large",
                "token limit",
            )
        ):
            return "context"

        if any(
            token in message
            for token in (
                "timeout",
                "timed out",
                "connection",
                "connection reset",
                "temporarily unavailable",
                "service unavailable",
                "bad gateway",
                "gateway timeout",
                "server error",
            )
        ):
            return "temporary"

        return "unknown"

    # ------------------------------------------------------------------
    # Response normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_content(response: Any) -> str:
        """
        Normalize all providers to the router's historical `str` contract.

        GroqProvider returns a normalized dictionary.
        Older providers may return a raw string.
        """

        if isinstance(response, str):
            content = response

        elif isinstance(response, dict):
            content = response.get("content")

            if content is None:
                content = response.get("text")

            if content is None:
                choices = response.get("choices")

                if choices:
                    first = choices[0]

                    if isinstance(first, dict):
                        message = first.get("message")

                        if isinstance(message, dict):
                            content = message.get("content")

                        if content is None:
                            content = first.get("text")

            if content is None:
                content = ""

        else:
            content = getattr(response, "content", None)

            if content is None:
                content = getattr(response, "text", None)

            if content is None:
                content = ""

        if not isinstance(content, str):
            content = str(content)

        content = content.strip()

        if not content:
            raise RoutingError("Provider returned an empty response.")

        return content

    # ------------------------------------------------------------------
    # Single model call
    # ------------------------------------------------------------------

    def _call_model(
        self,
        model: ModelDefinition,
        messages: Sequence[Dict[str, Any]],
        **kwargs: Any,
    ) -> str:

        provider = self.providers.get(model.provider)

        if provider is None:
            raise PermanentModelError(
                f"Provider '{model.provider}' is not configured."
            )

        if not self._provider_available(provider):
            raise TemporaryProviderError(
                f"Provider '{model.provider}' is unavailable."
            )

        max_tokens = kwargs.get(
            "max_tokens",
            model.max_tokens,
        )

        timeout_seconds = kwargs.get(
            "timeout_seconds",
            model.timeout,
        )

        generate_kwargs: Dict[str, Any] = {
            "messages": list(messages),
            "model": model.model_id,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": max_tokens,
            "timeout_seconds": timeout_seconds,
        }

        # Preserve optional arguments only when supplied.
        optional_keys = (
            "response_format",
            "top_p",
            "stop",
            "seed",
            "reasoning_effort",
            "include_reasoning",
            "tools",
            "tool_choice",
            "parallel_tool_calls",
        )

        for key in optional_keys:
            if key in kwargs and kwargs[key] is not None:
                generate_kwargs[key] = kwargs[key]

        started = time.perf_counter()

        try:
            response = provider.generate(**generate_kwargs)

            latency_ms = (
                time.perf_counter() - started
            ) * 1000.0

            content = self._extract_content(response)

            self.registry.mark_success(
                model.model_id,
                latency=latency_ms,
            )

            logger.info(
                "LLM success provider=%s model=%s latency_ms=%.0f",
                model.provider,
                model.model_id,
                latency_ms,
            )

            return content

        except Exception as exc:
            category = self._classify_error(exc)

            logger.warning(
                "LLM failure provider=%s model=%s category=%s error=%s",
                model.provider,
                model.model_id,
                category,
                exc,
            )

            if category == "rate_limit":
                self.registry.update_health(
                    model.model_id,
                    ModelHealthStatus.DEGRADED,
                    error=f"rate_limit: {exc}",
                )
                raise RateLimitError(str(exc)) from exc

            if category == "context":
                self.registry.update_health(
                    model.model_id,
                    ModelHealthStatus.DEGRADED,
                    error=f"context: {exc}",
                )
                raise ContextTooLargeError(str(exc)) from exc

            if category == "permanent":
                self.registry.update_health(
                    model.model_id,
                    ModelHealthStatus.UNHEALTHY,
                    error=str(exc),
                )
                raise PermanentModelError(str(exc)) from exc

            if category == "temporary":
                self.registry.update_health(
                    model.model_id,
                    ModelHealthStatus.DEGRADED,
                    error=str(exc),
                )
                raise TemporaryProviderError(str(exc)) from exc

            self.registry.update_health(
                model.model_id,
                ModelHealthStatus.DEGRADED,
                error=str(exc),
            )

            raise RoutingError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Public route API
    # ------------------------------------------------------------------

    def route(
        self,
        task: str | LLMTask,
        messages: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> str:
        """
        Execute a task through the configured fallback chain.

        The exact same `messages` are passed to every fallback model.
        Therefore a rate limit on GPT-OSS 120B does not cause the task
        to restart from scratch on GPT-OSS 20B.
        """

        task_enum = self._normalize_task(task)

        candidates = self._candidate_models(task_enum)

        if not candidates:
            raise RuntimeError(
                f"No eligible LLM models for task '{task_enum.value}'."
            )

        last_error: Optional[Exception] = None

        for model in candidates:
            if not model.enabled:
                continue

            # Registry cooldown/health gate.
            if not self._model_eligible(model):
                continue

            try:
                return self._call_model(
                    model,
                    messages,
                    **kwargs,
                )

            except Exception as exc:
                last_error = exc

                # IMPORTANT:
                # Every failure moves directly to the next eligible
                # candidate. No task restart and no destructive mutation.
                continue

        raise RuntimeError(
            f"All LLM models failed for task '{task_enum.value}'. "
            f"Last error: {last_error}"
        ) from last_error

    # ------------------------------------------------------------------
    # Context-aware route API
    # ------------------------------------------------------------------

    def route_with_context(
        self,
        context: RouteContext,
        **kwargs: Any,
    ) -> str:
        """
        Route using an explicit resumable context.

        This is the API we can use later for the full autonomous SourceAI
        research agent when work consists of multiple checkpoints.
        """

        context.attempts += 1

        task_enum = self._normalize_task(context.task)
        candidates = self._candidate_models(task_enum)

        if not candidates:
            raise RuntimeError(
                f"No eligible LLM models for task '{task_enum.value}'."
            )

        last_error: Optional[Exception] = None

        for model in candidates:
            if not model.enabled:
                continue

            if not self._model_eligible(model):
                continue

            try:
                content = self._call_model(
                    model,
                    context.messages,
                    **kwargs,
                )

                context.last_provider = model.provider
                context.last_model = model.model_id
                context.previous_output = content

                return content

            except Exception as exc:
                last_error = exc

                context.failures.append(
                    {
                        "provider": model.provider,
                        "model": model.model_id,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )

                continue

        raise RuntimeError(
            f"All LLM models failed for task '{task_enum.value}'. "
            f"Last error: {last_error}"
        ) from last_error

    # ------------------------------------------------------------------
    # Eligibility
    # ------------------------------------------------------------------

    def _model_eligible(self, model: ModelDefinition) -> bool:
        """
        UNKNOWN is intentionally eligible.

        We do not waste free API quota by probing every model before use.
        A real request itself becomes the health signal.
        """

        if not model.enabled:
            return False

        now = time.time()

        cooldown_until = getattr(
            model,
            "cooldown_until",
            None,
        )

        if cooldown_until is not None:
            try:
                if float(cooldown_until) > now:
                    return False
            except (TypeError, ValueError):
                pass

        if model.health_status == ModelHealthStatus.UNAVAILABLE:
            return False

        if model.health_status == ModelHealthStatus.COOLDOWN:
            if cooldown_until is not None:
                try:
                    if float(cooldown_until) > now:
                        return False
                except (TypeError, ValueError):
                    pass

        return True

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def routing_candidates(
        self,
        task: str | LLMTask,
    ) -> List[Dict[str, Any]]:
        """Return the current routing chain without making an API call."""

        task_enum = self._normalize_task(task)

        return [
            {
                "provider": model.provider,
                "model": model.model_id,
                "priority": model.priority,
                "health": (
                    model.health_status.value
                    if hasattr(model.health_status, "value")
                    else str(model.health_status)
                ),
                "enabled": model.enabled,
            }
            for model in self._candidate_models(task_enum)
        ]

    def has_qwen_models(self) -> bool:
        """
        Safety invariant.

        Returns True if Qwen has somehow entered the active registry.
        Production tests should assert this is False.
        """

        return any(
            "qwen" in model.model_id.lower()
            for model in self.registry.all_models()
        )
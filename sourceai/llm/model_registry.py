# sourceai/llm/model_registry.py

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class ModelCapability(str, Enum):
    """
    Capabilities used by SourceAI when selecting a model.
    """

    FAST = "fast"
    REASONING = "reasoning"
    SECURITY = "security"
    EXTRACTION = "extraction"
    GENERAL = "general"


class ModelHealthStatus(str, Enum):
    """
    Runtime health state of a model.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    COOLDOWN = "cooldown"
    UNKNOWN = "unknown"


@dataclass
class ModelDefinition:
    """
    Metadata and runtime state for one LLM model.
    """

    model_id: str

    provider: str

    display_name: str

    capabilities: List[ModelCapability]

    task_categories: List[str] = field(
        default_factory=list
    )

    # Higher priority = preferred model.
    priority: int = 0

    fallback_priority: int = 0

    timeout: int = 30

    max_tokens: int = 1024

    supports_json: bool = True

    supports_reasoning: bool = False

    security_role: Optional[str] = None

    enabled: bool = True

    health_status: ModelHealthStatus = (
        ModelHealthStatus.UNKNOWN
    )

    last_health_check: Optional[datetime] = None

    latency_ms: float = 0.0

    failure_count: int = 0

    cooldown_until: Optional[datetime] = None

    last_error: Optional[str] = None


class ModelRegistry:
    """
    Central in-process registry for SourceAI models.

    The registry is intentionally restricted to the models SourceAI
    actually supports.

    IMPORTANT:
        Qwen models are NOT registered here.
    """

    _instance: Optional["ModelRegistry"] = None

    _models: Dict[str, ModelDefinition] = {}

    def __new__(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            cls._instance._models = {}

            cls._instance._register_core_models()

        return cls._instance

    # ------------------------------------------------------------------
    # CORE MODEL REGISTRATION
    # ------------------------------------------------------------------

    def _register_core_models(self) -> None:
        """
        Register SourceAI's supported models.

        Priority:

            100  Groq GPT-OSS 120B
             90  Groq GPT-OSS 20B
             80  OpenRouter Nemotron
             70  OmniRoute Auto

        Security models are kept separately.
        """

        # ==============================================================
        # GROQ — PRIMARY
        # ==============================================================

        self.register(
            ModelDefinition(
                model_id="openai/gpt-oss-120b",
                provider="groq",
                display_name="GPT-OSS 120B",
                capabilities=[
                    ModelCapability.GENERAL,
                    ModelCapability.REASONING,
                    ModelCapability.EXTRACTION,
                ],
                priority=100,
                fallback_priority=100,
                supports_json=True,
                supports_reasoning=True,
                enabled=True,
                timeout=60,
                max_tokens=4096,
            )
        )

        # ==============================================================
        # GROQ — FALLBACK
        # ==============================================================

        self.register(
            ModelDefinition(
                model_id="openai/gpt-oss-20b",
                provider="groq",
                display_name="GPT-OSS 20B",
                capabilities=[
                    ModelCapability.FAST,
                    ModelCapability.GENERAL,
                    ModelCapability.REASONING,
                    ModelCapability.EXTRACTION,
                ],
                priority=90,
                fallback_priority=90,
                supports_json=True,
                supports_reasoning=True,
                enabled=True,
                timeout=45,
                max_tokens=4096,
            )
        )

        # ==============================================================
        # OPENROUTER — FALLBACK
        # ==============================================================

        self.register(
            ModelDefinition(
                model_id="nvidia/nemotron-3.5-lightning:free",
                provider="openrouter",
                display_name=(
                    "Nemotron 3.5 Lightning Free"
                ),
                capabilities=[
                    ModelCapability.GENERAL,
                    ModelCapability.REASONING,
                    ModelCapability.EXTRACTION,
                ],
                priority=80,
                fallback_priority=80,
                supports_json=False,
                supports_reasoning=True,
                enabled=True,
                timeout=60,
                max_tokens=4096,
            )
        )

        # ==============================================================
        # OMNIROUTE — FALLBACK
        # ==============================================================

        self.register(
            ModelDefinition(
                model_id="auto",
                provider="omniroute",
                display_name="OmniRoute Auto",
                capabilities=[
                    ModelCapability.FAST,
                    ModelCapability.GENERAL,
                    ModelCapability.REASONING,
                    ModelCapability.EXTRACTION,
                ],
                priority=70,
                fallback_priority=70,
                supports_json=True,
                supports_reasoning=True,
                enabled=True,
                timeout=60,
                max_tokens=4096,
            )
        )

        # ==============================================================
        # SECURITY — PROMPT GUARD
        # ==============================================================

        self.register(
            ModelDefinition(
                model_id=(
                    "meta-llama/"
                    "llama-prompt-guard-2-86m"
                ),
                provider="groq",
                display_name="Prompt Guard 86M",
                capabilities=[
                    ModelCapability.SECURITY
                ],
                priority=100,
                fallback_priority=100,
                supports_json=True,
                supports_reasoning=False,
                security_role="prompt_guard",
                enabled=True,
                timeout=30,
                max_tokens=512,
            )
        )

        self.register(
            ModelDefinition(
                model_id=(
                    "meta-llama/"
                    "llama-prompt-guard-2-22m"
                ),
                provider="groq",
                display_name="Prompt Guard 22M",
                capabilities=[
                    ModelCapability.SECURITY
                ],
                priority=90,
                fallback_priority=90,
                supports_json=True,
                supports_reasoning=False,
                security_role="prompt_guard",
                enabled=True,
                timeout=30,
                max_tokens=512,
            )
        )

    # ------------------------------------------------------------------
    # REGISTRATION
    # ------------------------------------------------------------------

    def register(
        self,
        model: ModelDefinition,
    ) -> None:
        """
        Add or replace a model definition.
        """

        self._models[model.model_id] = model

    # ------------------------------------------------------------------
    # LOOKUP
    # ------------------------------------------------------------------

    def get(
        self,
        model_id: str,
    ) -> Optional[ModelDefinition]:
        """
        Get one model by ID.
        """

        return self._models.get(model_id)

    def all_models(self) -> List[ModelDefinition]:
        """
        Return all registered models.
        """

        return list(self._models.values())

    # ------------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------------

    def get_healthy(
        self,
        capability: Optional[ModelCapability] = None,
        provider: Optional[str] = None,
    ) -> List[ModelDefinition]:
        """
        Return models currently considered healthy.

        Models in cooldown are excluded until their cooldown expires.
        """

        now = datetime.now()

        healthy: List[ModelDefinition] = []

        for model in self._models.values():

            if not model.enabled:
                continue

            if provider and model.provider != provider:
                continue

            # ----------------------------------------------------------
            # COOLDOWN
            # ----------------------------------------------------------

            if (
                model.health_status
                == ModelHealthStatus.COOLDOWN
            ):
                if (
                    model.cooldown_until
                    and model.cooldown_until > now
                ):
                    continue

                # Cooldown expired.
                # It can be attempted again.
                model.health_status = (
                    ModelHealthStatus.UNKNOWN
                )

            # ----------------------------------------------------------
            # HEALTH
            # ----------------------------------------------------------

            if model.health_status not in (
                ModelHealthStatus.HEALTHY,
                ModelHealthStatus.UNKNOWN,
            ):
                continue

            # ----------------------------------------------------------
            # CAPABILITY
            # ----------------------------------------------------------

            if (
                capability is not None
                and capability not in model.capabilities
            ):
                continue

            healthy.append(model)

        return sorted(
            healthy,
            key=lambda model: (
                -model.priority,
                model.latency_ms,
            ),
        )

    # ------------------------------------------------------------------
    # ENABLE / DISABLE
    # ------------------------------------------------------------------

    def enable(
        self,
        model_id: str,
    ) -> bool:
        """
        Enable a model.
        """

        model = self.get(model_id)

        if not model:
            return False

        model.enabled = True

        if model.health_status == (
            ModelHealthStatus.UNAVAILABLE
        ):
            model.health_status = (
                ModelHealthStatus.UNKNOWN
            )

        return True

    def disable(
        self,
        model_id: str,
    ) -> bool:
        """
        Permanently disable a model for the current process.
        """

        model = self.get(model_id)

        if not model:
            return False

        model.enabled = False

        return True

    # ------------------------------------------------------------------
    # HEALTH UPDATE
    # ------------------------------------------------------------------

    def update_health(
        self,
        model_id: str,
        status: ModelHealthStatus,
        latency: float = 0.0,
        error: Optional[str] = None,
        cooldown_seconds: int = 60,
    ) -> None:
        """
        Update runtime health state.

        This method is used by the router after real inference attempts.
        """

        model = self._models.get(model_id)

        if not model:
            return

        model.health_status = status

        model.last_health_check = datetime.now()

        if latency > 0:
            model.latency_ms = latency

        model.last_error = error

        # --------------------------------------------------------------
        # FAILURE HANDLING
        # --------------------------------------------------------------

        if status in (
            ModelHealthStatus.UNAVAILABLE,
            ModelHealthStatus.COOLDOWN,
            ModelHealthStatus.DEGRADED,
        ):
            model.failure_count += 1

        else:
            model.failure_count = 0
            model.last_error = None

        # --------------------------------------------------------------
        # COOLDOWN
        # --------------------------------------------------------------

        if status == ModelHealthStatus.COOLDOWN:

            model.cooldown_until = (
                datetime.now()
                + timedelta(
                    seconds=cooldown_seconds
                )
            )

        else:

            model.cooldown_until = None

    # ------------------------------------------------------------------
    # MARK SUCCESS
    # ------------------------------------------------------------------

    def mark_success(
        self,
        model_id: str,
        latency: float = 0.0,
    ) -> None:
        """
        Mark a model healthy after successful inference.
        """

        self.update_health(
            model_id=model_id,
            status=ModelHealthStatus.HEALTHY,
            latency=latency,
        )

    # ------------------------------------------------------------------
    # MARK FAILURE
    # ------------------------------------------------------------------

    def mark_failure(
        self,
        model_id: str,
        status: ModelHealthStatus = (
            ModelHealthStatus.DEGRADED
        ),
        error: Optional[str] = None,
        cooldown_seconds: int = 60,
        latency: float = 0.0,
    ) -> None:
        """
        Mark a model as failed.
        """

        self.update_health(
            model_id=model_id,
            status=status,
            latency=latency,
            error=error,
            cooldown_seconds=cooldown_seconds,
        )

    # ------------------------------------------------------------------
    # RESET
    # ------------------------------------------------------------------

    def reset_health(
        self,
        model_id: Optional[str] = None,
    ) -> None:
        """
        Reset health state for one model or all models.

        Useful for admin/testing operations.
        """

        models = (
            [self.get(model_id)]
            if model_id
            else self.all_models()
        )

        for model in models:

            if model is None:
                continue

            model.health_status = (
                ModelHealthStatus.UNKNOWN
            )

            model.last_health_check = None

            model.latency_ms = 0.0

            model.failure_count = 0

            model.cooldown_until = None

            model.last_error = None

    # ------------------------------------------------------------------
    # PROVIDER MODELS
    # ------------------------------------------------------------------

    def get_provider_models(
        self,
        provider: str,
    ) -> List[ModelDefinition]:
        """
        Return enabled models belonging to one provider.
        """

        provider = provider.strip().lower()

        return sorted(
            [
                model
                for model in self._models.values()
                if model.enabled
                and model.provider == provider
            ],
            key=lambda model: (
                -model.priority,
                model.latency_ms,
            ),
        )

    # ------------------------------------------------------------------
    # CAPABILITY MODELS
    # ------------------------------------------------------------------

    def get_capability_models(
        self,
        capability: ModelCapability,
    ) -> List[ModelDefinition]:
        """
        Return enabled models supporting a capability.
        """

        return sorted(
            [
                model
                for model in self._models.values()
                if model.enabled
                and capability in model.capabilities
            ],
            key=lambda model: (
                -model.priority,
                model.latency_ms,
            ),
        )
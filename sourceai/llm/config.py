# sourceai/llm/config.py

import os
from typing import List, Optional, Dict

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_FILE)


class LLMConfig(BaseModel):
    """
    Central configuration for SourceAI's LLM routing system.

    Provider priority:
        1. Groq
        2. OpenRouter
        3. OmniRoute

    Groq model priority:
        1. openai/gpt-oss-120b
        2. openai/gpt-oss-20b

    Qwen is intentionally NOT configured anywhere in SourceAI.
    """

    # ------------------------------------------------------------------
    # PROVIDER ORDER
    # ------------------------------------------------------------------

    provider_order: List[str] = Field(
        default_factory=lambda: [
            "groq",
            "openrouter",
            "omniroute",
        ],
        description=(
            "Ordered list of LLM providers used for automatic fallback."
        ),
    )

    # ------------------------------------------------------------------
    # GROQ
    # ------------------------------------------------------------------

    groq_api_key: Optional[str] = None

    # IMPORTANT:
    # GroqProvider uses the official Groq SDK, which handles the
    # /openai/v1/chat/completions path internally.
    groq_base_url: str = "https://api.groq.com/openai/v1"
    # Primary Groq model
    groq_default_model: str = "openai/gpt-oss-120b"

    # Ordered Groq fallbacks
    groq_fallback_models: List[str] = Field(
        default_factory=lambda: [
            "openai/gpt-oss-20b",
        ]
    )

    # ------------------------------------------------------------------
    # OPENCODE
    # ------------------------------------------------------------------
    #
    # Kept for compatibility with the existing project configuration.
    # It is NOT part of the default provider order.
    #

    opencode_api_key: Optional[str] = None
    opencode_base_url: Optional[str] = None
    opencode_default_model: str = "oc/big-pickle"

    # ------------------------------------------------------------------
    # OMNIROUTE
    # ------------------------------------------------------------------

    omniroute_api_key: Optional[str] = None
    omniroute_base_url: str = "http://localhost:20128/v1"
    omniroute_default_model: str = "auto"

    # ------------------------------------------------------------------
    # OPENROUTER
    # ------------------------------------------------------------------

    openrouter_api_key: Optional[str] = None

    openrouter_base_url: str = (
        "https://openrouter.ai/api/v1"
    )

    openrouter_default_model: str = (
        "nvidia/nemotron-3.5-lightning:free"
    )

    openrouter_reasoning_enabled: bool = True

    openrouter_http_referer: Optional[str] = None
    openrouter_x_title: Optional[str] = None

    # ------------------------------------------------------------------
    # GENERAL LLM SETTINGS
    # ------------------------------------------------------------------

    timeout_seconds: int = 60

    max_retries: int = 2

    # Optional per-task override.
    #
    # Example:
    #
    # {
    #     "supplier_extraction": "openai/gpt-oss-120b"
    # }
    #
    task_model_overrides: Dict[str, str] = Field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    @field_validator("provider_order")
    @classmethod
    def validate_provider_order(
        cls,
        value: List[str],
    ) -> List[str]:
        """
        Normalize provider names and remove duplicates.
        """

        normalized: List[str] = []

        for provider in value:
            provider = provider.strip().lower()

            if not provider:
                continue

            if provider not in normalized:
                normalized.append(provider)

        if not normalized:
            normalized = [
                "groq",
                "openrouter",
                "omniroute",
            ]

        return normalized

    @field_validator("groq_fallback_models")
    @classmethod
    def validate_groq_fallback_models(
        cls,
        value: List[str],
    ) -> List[str]:
        """
        Normalize Groq fallback models and prevent accidental
        duplication of the primary model.

        Qwen is intentionally rejected.
        """

        cleaned: List[str] = []

        for model in value:
            model = model.strip()

            if not model:
                continue

            # SourceAI must not use Qwen.
            if "qwen" in model.lower():
                continue

            if model not in cleaned:
                cleaned.append(model)

        return cleaned

    # ------------------------------------------------------------------
    # ENVIRONMENT LOADING
    # ------------------------------------------------------------------

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """
        Build LLM configuration from environment variables.
        """

        # --------------------------------------------------------------
        # PROVIDER ORDER
        # --------------------------------------------------------------

        provider_order_raw = os.getenv(
            "LLM_PROVIDER_ORDER",
            "groq,openrouter,omniroute",
        )

        provider_order = [
            provider.strip().lower()
            for provider in provider_order_raw.split(",")
            if provider.strip()
        ]

        # --------------------------------------------------------------
        # GROQ
        # --------------------------------------------------------------

        groq_key = (
            os.getenv("GROQ_API_KEY")
            or os.getenv("LLM_API_KEY")
        )

        groq_base = os.getenv(
            "GROQ_BASE_URL",
            "https://api.groq.com",
        )

        groq_model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b",
        )

        fallback_models_raw = os.getenv(
            "GROQ_FALLBACK_MODELS",
            "openai/gpt-oss-20b",
        )

        groq_fallback_models = [
            model.strip()
            for model in fallback_models_raw.split(",")
            if model.strip()
        ]

        # --------------------------------------------------------------
        # OPENCODE
        # --------------------------------------------------------------

        opencode_key = os.getenv(
            "OPENCODE_API_KEY"
        )

        opencode_base = os.getenv(
            "OPENCODE_BASE_URL"
        )

        opencode_model = os.getenv(
            "OPENCODE_MODEL",
            "oc/big-pickle",
        )

        # --------------------------------------------------------------
        # OMNIROUTE
        # --------------------------------------------------------------

        omniroute_key = os.getenv(
            "OMNIROUTE_API_KEY"
        )

        omniroute_base = os.getenv(
            "OMNIROUTE_BASE_URL",
            "http://localhost:20128/v1",
        )

        omniroute_model = os.getenv(
            "OMNIROUTE_MODEL",
            "auto",
        )

        # --------------------------------------------------------------
        # OPENROUTER
        # --------------------------------------------------------------

        openrouter_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

        openrouter_base = os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        )

        openrouter_model = os.getenv(
            "OPENROUTER_MODEL",
            "nvidia/nemotron-3.5-lightning:free",
        )

        openrouter_reasoning = (
            os.getenv(
                "OPENROUTER_REASONING_ENABLED",
                "true",
            ).lower()
            == "true"
        )

        openrouter_referer = os.getenv(
            "OPENROUTER_HTTP_REFERER"
        )

        openrouter_title = os.getenv(
            "OPENROUTER_X_TITLE"
        )

        # --------------------------------------------------------------
        # GENERAL SETTINGS
        # --------------------------------------------------------------

        timeout_seconds = int(
            os.getenv(
                "LLM_TIMEOUT_SECONDS",
                "60",
            )
        )

        max_retries = int(
            os.getenv(
                "LLM_MAX_RETRIES",
                "2",
            )
        )

        # --------------------------------------------------------------
        # TASK MODEL OVERRIDES
        # --------------------------------------------------------------

        task_model_overrides: Dict[str, str] = {}

        # Optional JSON object:
        #
        # LLM_TASK_MODEL_OVERRIDES='{"supplier_extraction":"openai/gpt-oss-120b"}'
        #
        overrides_raw = os.getenv(
            "LLM_TASK_MODEL_OVERRIDES"
        )

        if overrides_raw:
            try:
                import json

                parsed = json.loads(
                    overrides_raw
                )

                if isinstance(parsed, dict):
                    task_model_overrides = {
                        str(key): str(value)
                        for key, value in parsed.items()
                    }

            except (json.JSONDecodeError, TypeError, ValueError):
                # Do not crash the whole application because an optional
                # override variable is malformed.
                task_model_overrides = {}

        return cls(
            provider_order=provider_order,

            # Groq
            groq_api_key=groq_key,
            groq_base_url=groq_base,
            groq_default_model=groq_model,
            groq_fallback_models=groq_fallback_models,

            # OpenCode
            opencode_api_key=opencode_key,
            opencode_base_url=opencode_base,
            opencode_default_model=opencode_model,

            # OmniRoute
            omniroute_api_key=omniroute_key,
            omniroute_base_url=omniroute_base,
            omniroute_default_model=omniroute_model,

            # OpenRouter
            openrouter_api_key=openrouter_key,
            openrouter_base_url=openrouter_base,
            openrouter_default_model=openrouter_model,
            openrouter_reasoning_enabled=openrouter_reasoning,
            openrouter_http_referer=openrouter_referer,
            openrouter_x_title=openrouter_title,

            # General
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,

            # Task overrides
            task_model_overrides=task_model_overrides,
        )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def get_primary_provider(self) -> str:
        """
        Return the first configured provider.
        """

        if not self.provider_order:
            return "groq"

        return self.provider_order[0]

    def get_groq_models(self) -> List[str]:
        """
        Return the complete ordered Groq model chain.

        Example:
            [
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b"
            ]
        """

        models: List[str] = []

        if self.groq_default_model:
            models.append(
                self.groq_default_model
            )

        for model in self.groq_fallback_models:
            if model and model not in models:
                models.append(model)

        return models

    def get_provider_model(
        self,
        provider: str,
    ) -> Optional[str]:
        """
        Return the configured default model for a provider.
        """

        provider = provider.strip().lower()

        if provider == "groq":
            return self.groq_default_model

        if provider == "openrouter":
            return self.openrouter_default_model

        if provider == "omniroute":
            return self.omniroute_default_model

        if provider == "opencode":
            return self.opencode_default_model

        return None
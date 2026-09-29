# sourceai/llm/provider.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    @abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """Return available models from this provider."""
        ...

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        response_format: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """Send a completion request and return the response content."""
        ...

    @abstractmethod
    def health_check(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Check provider connectivity with a real inference request."""
        ...

    # ---- Non-abstract helpers (safe defaults, override if needed) ----

    def is_available(self) -> bool:
        """
        Return True if this provider is configured and ready.
        Override in subclasses for finer checks (e.g., key present, endpoint reachable).
        """
        return True

    def supports_model(self, model_id: str) -> bool:
        """Return True if this provider can serve the given model."""
        return True
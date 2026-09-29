# sourceai/llm/service.py
import logging
from typing import List, Dict, Any, Optional

from sourceai.llm.config import LLMConfig
from sourceai.llm import get_provider
from sourceai.llm.router import ModelRouter
from sourceai.llm.health import check_llm_health

logger = logging.getLogger(__name__)

class LLMService:
    """
    Facade for the LLM layer. Provides a simple interface for generating
    text with task‑specific model routing, health checks, and fallback handling.
    """
    _instance = None

    def __new__(cls, config: Optional[LLMConfig] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[LLMConfig] = None):
        if self._initialized:
            return
        self.config = config or LLMConfig.from_env()
        self.provider = get_provider(self.config)
        self.router = ModelRouter(self.config, self.provider)
        self._initialized = True

    def generate(
        self,
        task: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1024,
        response_format: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        """
        Generate a response for a given task and messages.
        Uses the model router to select the appropriate model.
        """
        return self.router.route(
            task=task,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            timeout_seconds=timeout_seconds,
        )

    def health(self) -> Dict[str, Any]:
        """
        Perform a real connectivity health check.
        """
        return check_llm_health(self.config)

    def get_routing_info(self, task: str) -> Dict[str, Any]:
        """
        Return the model that would be used for a given task (without making a request).
        """
        category = self.router.TASK_CATEGORIES.get(task, "default")
        model = self.router._select_model(task, category)
        return {
            "task": task,
            "category": category,
            "primary_model": model,
            "fallback_model": self.config.fallback_model,
        }


# Singleton instance for easy import
default_service = LLMService()
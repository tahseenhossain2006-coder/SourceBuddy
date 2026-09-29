# sourceai/llm/model_health.py
import time
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from .provider import LLMProvider   # ✅ fixed import

logger = logging.getLogger(__name__)

class ModelStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    COOLDOWN = "cooldown"
    UNKNOWN = "unknown"

@dataclass
class ModelHealth:
    model_id: str
    provider: str
    status: ModelStatus = ModelStatus.UNKNOWN
    last_checked: float = 0.0
    last_success: float = 0.0
    last_failure: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    latency_ms: float = 0.0
    last_error: Optional[str] = None
    cooldown_until: float = 0.0

class ModelHealthManager:
    def __init__(self, providers: Dict[str, LLMProvider], cooldown_config: Optional[Dict[str, int]] = None):
        self.providers = providers
        self.models: Dict[str, ModelHealth] = {}
        self.cooldown_config = cooldown_config or {
            "timeout": 60,
            "model_unavailable": 600,
            "http_429": 60,
            "http_5xx": 60,
            "network_error": 60,
            "auth_error": 300,
            "default": 60,
        }

    def discover_models(self):
        """Discover models from all providers."""
        for provider_name, provider in self.providers.items():
            try:
                raw_models = provider.list_models()
                for m in raw_models:
                    model_id = m.get("id")
                    if model_id and model_id not in self.models:
                        self.models[model_id] = ModelHealth(
                            model_id=model_id,
                            provider=provider_name
                        )
            except Exception as e:
                logger.warning(f"Discovery failed for provider {provider_name}: {e}")

    def probe_model(self, model_id: str) -> bool:
        health = self.models.get(model_id)
        if not health:
            return False
        provider = self.providers.get(health.provider)
        if not provider:
            return False
        try:
            result = provider.health_check(model=model_id)
            if result.get("real_inference", False):
                health.status = ModelStatus.HEALTHY
                health.last_success = time.time()
                health.consecutive_successes += 1
                health.consecutive_failures = 0
                health.latency_ms = result.get("latency_ms", 0)
                health.last_error = None
                health.cooldown_until = 0
                return True
            else:
                self._record_failure(model_id, result.get("error", "Probe failed"))
                return False
        except Exception as e:
            self._record_failure(model_id, str(e))
            return False

    def _record_failure(self, model_id: str, error_msg: str):
        health = self.models.get(model_id)
        if not health:
            return
        health.last_failure = time.time()
        health.consecutive_failures += 1
        health.consecutive_successes = 0
        health.last_error = error_msg
        cooldown = self._cooldown_for_error(error_msg)
        health.cooldown_until = time.time() + cooldown
        if health.consecutive_failures >= 3:
            health.status = ModelStatus.UNAVAILABLE
        else:
            health.status = ModelStatus.DEGRADED

    def _cooldown_for_error(self, error: str) -> int:
        error_lower = error.lower()
        if "timeout" in error_lower:
            return self.cooldown_config["timeout"]
        if "429" in error_lower:
            return self.cooldown_config["http_429"]
        if "5" in error_lower and "http" in error_lower:
            return self.cooldown_config["http_5xx"]
        if "network" in error_lower or "connection" in error_lower:
            return self.cooldown_config["network_error"]
        if "auth" in error_lower or "401" in error_lower or "403" in error_lower:
            return self.cooldown_config["auth_error"]
        if "model" in error_lower and "unavailable" in error_lower:
            return self.cooldown_config["model_unavailable"]
        return self.cooldown_config["default"]

    def get_healthy_models(self) -> List[ModelHealth]:
        now = time.time()
        healthy = []
        for m in self.models.values():
            if m.cooldown_until > now and m.status != ModelStatus.HEALTHY:
                m.status = ModelStatus.COOLDOWN
                continue
            if m.status == ModelStatus.HEALTHY:
                healthy.append(m)
        return sorted(healthy, key=lambda h: (h.latency_ms if h.latency_ms else 9999))

    def select_best_model(self) -> Optional[str]:
        healthy = self.get_healthy_models()
        if healthy:
            return healthy[0].model_id
        return None

    def report_status(self) -> Dict[str, Any]:
        return {
            "total_models": len(self.models),
            "healthy": [m.model_id for m in self.get_healthy_models()],
            "degraded": [m.model_id for m in self.models.values() if m.status == ModelStatus.DEGRADED],
            "unavailable": [m.model_id for m in self.models.values() if m.status == ModelStatus.UNAVAILABLE],
            "cooldown": [m.model_id for m in self.models.values() if m.status == ModelStatus.COOLDOWN],
        }
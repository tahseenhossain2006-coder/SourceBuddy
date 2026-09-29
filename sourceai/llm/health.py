# sourceai/llm/health.py
import time
import logging
import concurrent.futures
from typing import Dict, Optional, List, Any
from .provider import LLMProvider
from .model_registry import ModelRegistry, ModelHealthStatus, ModelDefinition, ModelCapability

logger = logging.getLogger(__name__)

class ModelHealthManager:
    def __init__(self, providers: Dict[str, LLMProvider], registry: ModelRegistry):
        self.providers = providers
        self.registry = registry

    def discover_models(self) -> None:
        for provider_name, provider in self.providers.items():
            try:
                models = provider.list_models()
                for m in models:
                    model_id = m.get("id")
                    if not model_id or model_id in self.registry._models:
                        continue
                    caps = [ModelCapability.GENERAL]
                    if "reason" in model_id.lower() or "nemotron" in model_id.lower():
                        caps.append(ModelCapability.REASONING)
                    if "guard" in model_id.lower() or "prompt" in model_id.lower():
                        caps.append(ModelCapability.SECURITY)
                    self.registry.register(ModelDefinition(
                        model_id=model_id,
                        provider=provider_name,
                        display_name=model_id,
                        capabilities=caps,
                        enabled=True,
                        timeout=30,
                        max_tokens=1024,
                        health_status=ModelHealthStatus.UNKNOWN,
                    ))
            except Exception as e:
                logger.warning(f"Discovery failed for {provider_name}: {e}")

    def probe_model(self, model_id: str) -> bool:
        model_def = self.registry.get(model_id)
        if not model_def:
            return False
        provider = self.providers.get(model_def.provider)
        if not provider:
            self.registry.update_health(model_id, ModelHealthStatus.UNAVAILABLE, error="Provider unavailable")
            return False

        start = time.perf_counter()
        try:
            # Use a thread to enforce a hard deadline
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    provider.generate,
                    messages=[{"role": "user", "content": "Reply with exactly: SOURCEAI_HEALTH_OK"}],
                    model=model_id,
                    max_tokens=10,
                    temperature=0.0
                )
                timeout = model_def.timeout or 30
                response = future.result(timeout=timeout)
            latency_ms = int((time.perf_counter() - start) * 1000)
            if "SOURCEAI_HEALTH_OK" in response:
                self.registry.update_health(model_id, ModelHealthStatus.HEALTHY, latency=latency_ms)
                return True
            else:
                self.registry.update_health(model_id, ModelHealthStatus.DEGRADED, latency=latency_ms,
                                            error=f"Unexpected response: {response[:50]}")
                return False
        except concurrent.futures.TimeoutError:
            latency_ms = int((time.perf_counter() - start) * 1000)
            self.registry.update_health(model_id, ModelHealthStatus.UNAVAILABLE, latency=latency_ms,
                                        error="Timeout during health check")
            return False
        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            self.registry.update_health(model_id, ModelHealthStatus.UNAVAILABLE, latency=latency_ms, error=str(e))
            return False

    def probe_all_models(self) -> Dict[str, bool]:
        results = {}
        for model_id in list(self.registry._models.keys()):
            try:
                results[model_id] = self.probe_model(model_id)
            except Exception as e:
                logger.error(f"Unexpected error probing {model_id}: {e}")
                results[model_id] = False
        return results

    def get_healthy_models(self, capability: Optional[str] = None) -> List[str]:
        healthy = self.registry.get_healthy()
        if capability:
            try:
                cap_enum = ModelCapability(capability)
                healthy = [m for m in healthy if cap_enum in m.capabilities]
            except ValueError:
                pass
        return [m.model_id for m in healthy]
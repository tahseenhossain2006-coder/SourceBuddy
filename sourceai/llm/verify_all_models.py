# sourceai/llm/verify_all_models.py
import sys
import os
from dotenv import load_dotenv
load_dotenv()

from .config import LLMConfig
from .provider_factory import get_all_providers
from .model_registry import ModelRegistry, ModelHealthStatus
from .health import ModelHealthManager

def main():
    print("\n# SOURCEAI LLM SYSTEM VERIFICATION")
    print("===================================\n")
    config = LLMConfig.from_env()
    print(f"Provider order: {config.provider_order}")
    print()

    providers = get_all_providers(config)
    if not providers:
        print("❌ No providers configured.")
        sys.exit(1)

    print(f"Configured providers: {list(providers.keys())}\n")

    registry = ModelRegistry()
    health_manager = ModelHealthManager(providers, registry=registry)
    health_manager.discover_models()
    health_manager.probe_all_models()

    healthy = registry.get_healthy()
    degraded = [m for m in registry._models.values() if m.health_status == ModelHealthStatus.DEGRADED]
    unavailable = [m for m in registry._models.values() if m.health_status == ModelHealthStatus.UNAVAILABLE]

    print("SUMMARY")
    print("-------")
    print(f"Total registered models: {len(registry._models)}")
    print(f"Healthy models: {len(healthy)}")
    print(f"Degraded models: {len(degraded)}")
    print(f"Unavailable models: {len(unavailable)}")

    if healthy:
        print("\n🟢 Healthy models:")
        for m in healthy:
            print(f"  {m.display_name} ({m.model_id}) - {m.provider}")
    if degraded:
        print("\n🟡 Degraded models:")
        for m in degraded:
            print(f"  {m.display_name} ({m.model_id}) - {m.provider}")
    if unavailable:
        print("\n🔴 Unavailable models:")
        for m in unavailable:
            print(f"  {m.display_name} ({m.model_id}) - {m.provider}")

    # Provider-level summary
    provider_health = {}
    for pname in providers.keys():
        pmodels = [m for m in registry._models.values() if m.provider == pname]
        healthy_count = sum(1 for m in pmodels if m.health_status == ModelHealthStatus.HEALTHY)
        total = len(pmodels)
        status = "HEALTHY" if healthy_count == total and total > 0 else "DEGRADED" if healthy_count > 0 else "UNAVAILABLE"
        provider_health[pname] = f"{status} ({healthy_count}/{total})"

    print("\nProvider health:")
    for name, status in provider_health.items():
        print(f"  {name}: {status}")

    if healthy:
        print("\n✅ SYSTEM VERIFICATION PASSED")
        sys.exit(0)
    else:
        print("\n❌ SYSTEM VERIFICATION FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
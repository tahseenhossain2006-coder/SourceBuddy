#!/usr/bin/env python
import sys
from .config import LLMConfig
from . import get_providers
from .model_health import ModelHealthManager

def main():
    print("\n# SOURCEAI MULTI-PROVIDER HEALTH")
    print("===================================")
    config = LLMConfig.from_env()
    
    # Instantiate providers based on config
    providers = get_providers(config)
    print(f"Providers configured: {list(providers.keys())}")
    
    manager = ModelHealthManager(providers)
    manager.discover_models()
    print(f"Discovered models: {len(manager.models)}")
    
    # Probe all models
    healthy = []
    for model_id in list(manager.models.keys()):
        print(f"Probing {model_id} ... ", end="", flush=True)
        if manager.probe_model(model_id):
            health = manager.models[model_id]
            print(f"🟢 HEALTHY ({health.latency_ms:.0f}ms)")
            healthy.append(model_id)
        else:
            health = manager.models[model_id]
            print(f"🔴 UNAVAILABLE ({health.last_error or 'unknown'})")
    
    print("\nSUMMARY")
    print("-------")
    print(f"Total models: {len(manager.models)}")
    print(f"Healthy: {len(healthy)}")
    if healthy:
        print("Primary candidate:", healthy[0])
        sys.exit(0)
    else:
        print("No healthy models found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
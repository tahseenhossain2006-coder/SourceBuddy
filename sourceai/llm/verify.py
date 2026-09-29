#!/usr/bin/env python
import sys
import json
from .config import LLMConfig
from . import get_provider
from .router import ModelRouter, TASK_CATEGORIES

def verify_connectivity():
    print("🔍 LLM Connectivity Verification")
    config = LLMConfig.from_env()
    try:
        provider = get_provider(config)
        result = provider.health_check()
        if result.get("connected"):
            print(f"✅ CONNECTED to {result['provider']} with model {result['model']}")
            print(f"   Latency: {result.get('latency_ms')}ms")
            print(f"   Real inference: {result.get('real_inference')}")
            sys.exit(0)
        else:
            print(f"❌ FAILED: {result.get('error')}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        sys.exit(1)

def verify_routing():
    print("🔍 LLM Routing Verification")
    config = LLMConfig.from_env()
    provider = get_provider(config)
    router = ModelRouter(config, provider)
    test_tasks = [
        "requirement_extraction",
        "evidence_verification",
        "supplier_comparison",
        "summarization"
    ]
    all_pass = True
    for task in test_tasks:
        try:
            # Simple test message
            response = router.route(
                task=task,
                messages=[{"role": "user", "content": f"Reply with the word 'OK' for task {task}"}],
                max_tokens=10
            )
            print(f"✅ {task}: OK (response: {response[:50]})")
        except Exception as e:
            print(f"❌ {task}: FAILED - {e}")
            all_pass = False
    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "routing":
        verify_routing()
    else:
        verify_connectivity()
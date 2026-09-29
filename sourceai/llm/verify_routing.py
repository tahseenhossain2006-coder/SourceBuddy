#!/usr/bin/env python
# sourceai/llm/verify_routing.py
"""
SourceAI LLM Routing Verification

Tests task-specific model routing for all defined tasks.
For each task, it attempts a real inference request and reports:
- task name
- selected primary model (according to routing matrix)
- provider used
- success/failure
- latency (if success)
- fallback count (if any)
"""

import sys
import time
import logging
from typing import Dict, Any, List, Optional

from .config import LLMConfig
from . import get_providers
from .model_registry import ModelRegistry, ModelDefinition, ModelCapability, ModelHealthStatus
from .router import ModelRouter
from .tasks import LLMTask, TASK_MODEL_MAP

logging.basicConfig(level=logging.WARNING)  # reduce noise
logger = logging.getLogger(__name__)


def register_models(registry: ModelRegistry, config: LLMConfig):
    """Register all models that the router should know about."""
    # Groq models
    groq_models = [
        ("qwen/qwen3.6-27b", "Qwen 3.6 (Fast)", [ModelCapability.FAST, ModelCapability.GENERAL], 10),
        ("qwen/qwen3.8-27b", "Qwen 3.8 (Fallback)", [ModelCapability.FAST, ModelCapability.GENERAL], 8),
        ("allam-2-7b", "Allam 2 (Fast)", [ModelCapability.FAST], 6),
        ("groq/compound-mini", "Groq Compound Mini", [ModelCapability.FAST], 5),
    ]
    for model_id, display_name, caps, priority in groq_models:
        registry.register(ModelDefinition(
            model_id=model_id,
            provider="groq",
            display_name=display_name,
            capabilities=caps,
            task_categories=[],
            priority=priority,
            supports_reasoning=False,
            enabled=True,
            health_status=ModelHealthStatus.UNKNOWN,
            timeout=config.timeout_seconds,
            max_tokens=1024,
        ))

    # OmniRoute model (Nemotron)
    registry.register(ModelDefinition(
        model_id="nemotron-3-ultra-free",
        provider="omniroute",
        display_name="Nemotron 3 Ultra (Reasoning)",
        capabilities=[ModelCapability.REASONING],
        task_categories=[],
        priority=20,
        supports_reasoning=True,
        enabled=True,
        health_status=ModelHealthStatus.UNKNOWN,
        timeout=config.timeout_seconds,
        max_tokens=2048,
    ))

    # Prompt Guard models
    registry.register(ModelDefinition(
        model_id="meta-llama/llama-prompt-guard-2-86m",
        provider="groq",
        display_name="Prompt Guard 86M (Security)",
        capabilities=[ModelCapability.SECURITY],
        task_categories=[],
        priority=10,
        security_role="prompt_guard",
        enabled=True,
        health_status=ModelHealthStatus.UNKNOWN,
        timeout=config.timeout_seconds,
        max_tokens=512,
    ))
    registry.register(ModelDefinition(
        model_id="meta-llama/llama-prompt-guard-2-22m",
        provider="groq",
        display_name="Prompt Guard 22M (Security)",
        capabilities=[ModelCapability.SECURITY],
        task_categories=[],
        priority=5,
        security_role="prompt_guard",
        enabled=True,
        health_status=ModelHealthStatus.UNKNOWN,
        timeout=config.timeout_seconds,
        max_tokens=512,
    ))


def test_task(router: ModelRouter, task: LLMTask) -> Dict[str, Any]:
    """Test a single task with a minimal inference request."""
    start = time.perf_counter()
    try:
        # Use a very short message to test routing
        response = router.route(
            task.value,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
            temperature=0.0
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        success = "ok" in response.lower()
        return {
            "task": task.value,
            "success": success,
            "latency_ms": latency_ms,
            "response": response.strip()[:50] + ("..." if len(response) > 50 else ""),
        }
    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "task": task.value,
            "success": False,
            "latency_ms": latency_ms,
            "error": str(e),
        }


def main():
    print("\n# SOURCEAI LLM ROUTING VERIFICATION")
    print("====================================\n")

    # Load configuration
    config = LLMConfig.from_env()
    print(f"Provider order: {config.provider_order}")
    print()

    # Instantiate providers
    providers = get_providers(config)
    if not providers:
        print("❌ No providers configured. Please set environment variables.")
        sys.exit(1)

    # Create registry and register models
    registry = ModelRegistry()
    register_models(registry, config)

    # Create router
    router = ModelRouter(config, providers)

    # Test all tasks defined in TASK_MODEL_MAP
    tasks_to_test = list(TASK_MODEL_MAP.keys())
    print(f"Testing {len(tasks_to_test)} tasks...\n")

    results = []
    for task in tasks_to_test:
        print(f"Testing task: {task.value} ... ", end="", flush=True)
        result = test_task(router, task)
        results.append(result)
        if result["success"]:
            print(f"✅ PASS ({result['latency_ms']} ms)")
        else:
            print(f"❌ FAIL ({result.get('error', 'unknown')})")

    # Summary
    print("\nSUMMARY")
    print("-------")
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    print(f"Tasks tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")

    if passed == total:
        print("\n✅ ROUTING VERIFICATION PASSED")
        sys.exit(0)
    else:
        print("\n❌ ROUTING VERIFICATION FAILED")
        # List failed tasks
        failed = [r for r in results if not r["success"]]
        for f in failed:
            print(f"  - {f['task']}: {f.get('error', 'unknown')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
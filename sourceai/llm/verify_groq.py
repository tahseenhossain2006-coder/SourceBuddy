#!/usr/bin/env python
# sourceai/llm/verify_groq.py
import os
import sys
import traceback

# Ensure dotenv is installed; if not, skip loading .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# We must import the modules relative to sourceai.llm
try:
    from .groq_provider import GroqProvider
    from .model_health import ModelHealthManager, ModelStatus, ModelHealth
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the file is placed in sourceai/llm/ and the package structure is correct.")
    sys.exit(1)

def main():
    print("\n# GROQ HEALTH")
    print("=============")

    api_key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not set. Please set it in your environment or .env file.")
        sys.exit(1)

    key_preview = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else api_key
    print(f"API key loaded: YES (starts with: {key_preview})")
    if not api_key.startswith("gsk_"):
        print("⚠️  Warning: API key does not start with 'gsk_'.")

    base_url = os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
    print(f"Endpoint: {base_url}")

    # Determine which model to test
    test_model = os.getenv("GROQ_MODEL")
    if not test_model:
        test_model = "llama-3.3-70b-versatile"  # fallback
        print(f"⚠️  GROQ_MODEL not set, using fallback: {test_model}")
    else:
        print(f"Using GROQ_MODEL: {test_model}")

    print()  # blank line

    provider = GroqProvider(
        api_key=api_key,
        base_url=base_url,
        default_timeout=30
    )

    # Test connectivity with the selected model
    print(f"Testing connectivity with `{test_model}`...")
    health = provider.health_check(model=test_model)
    if health.get("real_inference"):
        print("✅ Connectivity works.")
    else:
        error = health.get("error", "unknown error")
        print(f"❌ Connectivity failed: {error}")
        print("\nPossible causes:")
        print("  - The model may be unavailable or deprecated.")
        print("  - Invalid or expired Groq API key.")
        print("  - Key does not have permission for the /models endpoint.")
        print("  - Network/firewall blocking outbound requests.")
        sys.exit(1)

    # Now discover models
    print("\nDiscovering models from Groq...")
    try:
        raw_models = provider.list_models()
    except Exception as e:
        print(f"❌ Failed to discover models: {e}")
        sys.exit(1)

    if not raw_models:
        print("❌ No models discovered. The API key may not have access to the /models endpoint.")
        sys.exit(1)

    all_model_ids = [m.get("id") for m in raw_models if m.get("id")]
    discovered_count = len(all_model_ids)

    max_probes = int(os.getenv("GROQ_MAX_HEALTH_PROBES", "10"))
    candidates = all_model_ids[:max_probes]
    tested_count = len(candidates)

    print(f"Discovered models: {discovered_count}")
    print(f"Testing candidates: {tested_count}\n")

    manager = ModelHealthManager({"groq": provider})
    for mid in candidates:
        if mid not in manager.models:
            manager.models[mid] = ModelHealth(model_id=mid, provider="groq")
        success = manager.probe_model(mid)
        health = manager.models[mid]
        if success:
            print(f"🟢 {mid} — HEALTHY — {health.latency_ms:.0f} ms")
        else:
            if health.status == ModelStatus.DEGRADED:
                print(f"🟡 {mid} — DEGRADED — {health.last_error}")
            else:
                print(f"🔴 {mid} — UNAVAILABLE — {health.last_error or 'unknown'}")

    healthy = [m for m in manager.models.values() if m.status == ModelStatus.HEALTHY]
    degraded = [m for m in manager.models.values() if m.status == ModelStatus.DEGRADED]
    unavailable = [m for m in manager.models.values() if m.status == ModelStatus.UNAVAILABLE]

    print("\n## SUMMARY")
    print(f"Discovered models: {discovered_count}")
    print(f"Tested candidates: {tested_count}")
    print(f"Healthy models: {len(healthy)}")
    print(f"Degraded models: {len(degraded)}")
    print(f"Unavailable models: {len(unavailable)}")

    if len(healthy) > 0:
        print("\n✅ GROQ HEALTH: PASS")
        sys.exit(0)
    else:
        print("\n❌ GROQ HEALTH: FAIL")
        print("No healthy Groq models found. Check your API key and model availability.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Unhandled exception: {e}")
        traceback.print_exc()
        sys.exit(1)
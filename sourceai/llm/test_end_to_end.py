# sourceai/llm/test_end_to_end.py
import sys
import json
from sourceai.llm.config import LLMConfig
from sourceai.llm.provider_factory import get_all_providers
from sourceai.llm.router import ModelRouter
from sourceai.llm.tasks import LLMTask
from sourceai.llm.integration import LLMIntegration

def main():
    print("\n# SOURCEAI LLM E2E TEST")
    print("=======================\n")
    config = LLMConfig.from_env()
    providers = get_all_providers(config)
    if not providers:
        print("❌ No providers configured.")
        sys.exit(1)
    router = ModelRouter(config, providers)
    integration = LLMIntegration(router)

    user_query = "Find clothing manufacturers in India with MOQ below 500 units."
    print(f"Query: {user_query}\n")

    # Requirement understanding
    try:
        req = integration.understand_requirement(user_query)
        print(f"✅ Requirement understanding: {req}")
    except Exception as e:
        print(f"❌ Requirement understanding failed: {e}")
        sys.exit(1)

    # Intent detection (simplified)
    prompt = f"Classify intent of: {user_query}"
    try:
        response = router.route(LLMTask.INTENT_DETECTION.value, [{"role": "user", "content": prompt}], max_tokens=10)
        print(f"✅ Intent detection: {response.strip()}")
    except Exception as e:
        print(f"❌ Intent detection failed: {e}")
        sys.exit(1)

    # Final answer
    try:
        answer = integration.generate_final_answer([], req)
        print(f"✅ Final answer: {answer[:100]}...")
    except Exception as e:
        print(f"❌ Final answer generation failed: {e}")
        sys.exit(1)

    print("\n✅ E2E test passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
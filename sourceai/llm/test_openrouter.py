# sourceai/llm/test_openrouter.py
import os
from dotenv import load_dotenv
from sourceai.llm.config import LLMConfig
from sourceai.llm.openrouter_provider import OpenRouterProvider

# Load .env file
load_dotenv()

def main():
    config = LLMConfig.from_env()
    if not config.openrouter_api_key:
        print("❌ OPENROUTER_API_KEY not set. Please add it to .env or set it in your environment.")
        return
    provider = OpenRouterProvider(
        api_key=config.openrouter_api_key,
        base_url=config.openrouter_base_url,
        default_model=config.openrouter_default_model,
        reasoning_enabled=config.openrouter_reasoning_enabled,
        default_timeout=config.timeout_seconds,
        http_referer=config.openrouter_http_referer,
        x_title=config.openrouter_x_title,
    )
    print("Testing OpenRouter health...")
    result = provider.health_check()
    if result.get("real_inference"):
        print(f"✅ OpenRouter health check passed: {result}")
    else:
        print(f"❌ OpenRouter health check failed: {result}")

if __name__ == "__main__":
    main()
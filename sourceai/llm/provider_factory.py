 # sourceai/llm/provider_factory.py
from typing import Dict, Optional
from .provider import LLMProvider
from .groq_provider import GroqProvider
from .omniroute_provider import OmniRouteProvider
from .openrouter_provider import OpenRouterProvider
from .config import LLMConfig

def get_all_providers(config: Optional[LLMConfig] = None) -> Dict[str, LLMProvider]:
    """
    Instantiate all configured LLM providers based on their credentials.
    Does NOT depend on provider_order – the router uses the order separately.
    """
    config = config or LLMConfig.from_env()
    providers: Dict[str, LLMProvider] = {}

    # Groq
    if config.groq_api_key:
        providers["groq"] = GroqProvider(
            api_key=config.groq_api_key,
            base_url=config.groq_base_url,
            default_timeout=config.timeout_seconds,
        )

    # OpenRouter
    if config.openrouter_api_key:
        providers["openrouter"] = OpenRouterProvider(
            api_key=config.openrouter_api_key,
            base_url=config.openrouter_base_url,
            default_model=config.openrouter_default_model,
            reasoning_enabled=config.openrouter_reasoning_enabled,
            default_timeout=config.timeout_seconds,
            http_referer=config.openrouter_http_referer,
            x_title=config.openrouter_x_title,
        )

    # OmniRoute – instantiate if base_url is set (default is always set)
    providers["omniroute"] = OmniRouteProvider(
        api_key=config.omniroute_api_key,
        base_url=config.omniroute_base_url,
        default_timeout=config.timeout_seconds,
    )

    # Ollama (optional)
    if "ollama" in config.provider_order:
        try:
            from .ollama_provider import OllamaProvider
            providers["ollama"] = OllamaProvider(
                base_url=config.ollama_base_url if hasattr(config, "ollama_base_url") else "http://localhost:11434/v1",
                default_timeout=config.timeout_seconds,
            )
        except ImportError:
            pass

    return providers

def get_provider(provider_name: str, config: Optional[LLMConfig] = None) -> LLMProvider:
    providers = get_all_providers(config)
    name = provider_name.strip().lower()
    if name not in providers:
        raise ValueError(f"Provider '{provider_name}' not configured.")
    return providers[name]
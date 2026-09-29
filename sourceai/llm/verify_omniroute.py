#!/usr/bin/env python
# sourceai/llm/verify_omniroute.py

"""
SourceAI OmniRoute health verification.

Purpose:
    - Discover models from OmniRoute.
    - Exclude routing aliases such as auto/*.
    - Prefer known direct Groq/OpenCode candidates.
    - Perform REAL inference against each candidate.
    - Keep ONLY models that return a valid successful response.
    - Classify failures without treating them as usable models.
    - Stop early once enough healthy models are found.
    - Never report a model healthy without successful inference.

This verifier uses the CURRENT LLMConfig schema:
    omniroute_api_key
    omniroute_base_url
    omniroute_default_model
    timeout_seconds
    max_retries
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .config import LLMConfig
from .omniroute_provider import OmniRouteProvider


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_HEALTHY_TARGET = 3
DEFAULT_MAX_PROBES = 15

HEALTHY_TARGET = int(
    os.getenv("OMNIROUTE_HEALTHY_TARGET", str(DEFAULT_HEALTHY_TARGET))
)

MAX_PROBES = int(
    os.getenv("OMNIROUTE_MAX_PROBES", str(DEFAULT_MAX_PROBES))
)

HEALTH_TEST_PROMPT = "Reply with exactly OK."

# Models that have already been observed/recommended for SourceAI.
# They are only considered healthy after REAL inference succeeds.
KNOWN_PRIORITY_MODELS = [
    # Direct Groq models
    "groq/qwen/qwen3.6-27b",
    "groq/openai/gpt-oss-120b",
    "groq/openai/gpt-oss-20b",
    "groq/openai/gpt-oss-safeguard-20b",

    # OpenCode free models
    "oc/big-pickle",
    "oc/mimo-v2.5-free",
    "oc/nemotron-3-ultra-free",
    "oc/north-mini-code-free",
    "oc/hy3-free",
    "oc/deepseek-v4-flash-free",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HealthResult:
    model: str
    status: str
    latency_ms: Optional[int] = None
    error_type: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Model filtering
# ---------------------------------------------------------------------------

def is_direct_model(model_id: str) -> bool:
    """
    Return True only for actual model IDs.

    Excludes OmniRoute routing aliases such as:
        auto
        auto/*
    """
    if not model_id:
        return False

    normalized = model_id.strip().lower()

    if normalized == "auto":
        return False

    if normalized.startswith("auto/"):
        return False

    return True


def is_eligible_candidate(model_id: str) -> bool:
    """
    Decide whether a discovered model is worth probing.

    Important:
        Eligibility does NOT mean healthy.

    A model becomes healthy only after real inference succeeds.
    """
    if not is_direct_model(model_id):
        return False

    model = model_id.lower()

    # Known SourceAI candidates.
    if model in {m.lower() for m in KNOWN_PRIORITY_MODELS}:
        return True

    # Prefer free/keyless models.
    if model.startswith("oc/") and "free" in model:
        return True

    if "free" in model:
        return True

    # Avoid obvious non-LLM/video/control entries.
    excluded_patterns = [
        "veo",
        "seedance",
        "image",
        "embedding",
        "tts",
        "speech",
        "audio",
        "moderation",
        "rerank",
        "vision-only",
    ]

    if any(pattern in model for pattern in excluded_patterns):
        return False

    # Avoid obvious paid/proprietary models for the free launch setup.
    excluded_paid_patterns = [
        "claude",
        "gemini-pro",
        "gpt-4",
        "gpt-5",
        "paid",
        "enterprise",
    ]

    if any(pattern in model for pattern in excluded_paid_patterns):
        return False

    return True


def priority_score(model_id: str) -> int:
    """
    Higher score means earlier health probing.
    """

    model = model_id.lower()
    score = 0

    # Highest priority: models already known to be useful.
    known_priority = {
        "groq/qwen/qwen3.6-27b": 200,
        "groq/openai/gpt-oss-120b": 195,
        "groq/openai/gpt-oss-20b": 190,
        "groq/openai/gpt-oss-safeguard-20b": 170,

        "oc/big-pickle": 150,
        "oc/mimo-v2.5-free": 145,
        "oc/nemotron-3-ultra-free": 140,
        "oc/north-mini-code-free": 135,
        "oc/hy3-free": 130,
        "oc/deepseek-v4-flash-free": 125,
    }

    if model in known_priority:
        return known_priority[model]

    # Direct Groq models are preferred.
    if model.startswith("groq/"):
        score += 100

    # Free OpenCode models.
    if model.startswith("oc/"):
        score += 80

    if "free" in model:
        score += 30

    # Coding/reasoning names are useful for SourceAI.
    useful_keywords = [
        "qwen",
        "gpt-oss",
        "deepseek",
        "nemotron",
        "code",
        "coding",
        "reason",
        "coder",
    ]

    for keyword in useful_keywords:
        if keyword in model:
            score += 5

    return score


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

def classify_error(error: Exception) -> str:
    """
    Convert provider errors into stable categories.
    """

    message = str(error).lower()

    if "403" in message or "forbidden" in message:
        return "access_denied"

    if "401" in message or "unauthorized" in message:
        return "authentication"

    if "429" in message or "rate limit" in message or "rate_limit" in message:
        return "rate_limited"

    if "timeout" in message or "timed out" in message:
        return "timeout"

    if "model unavailable" in message:
        return "model_unavailable"

    if "not found" in message or "404" in message:
        return "not_found"

    if "connection" in message or "connection refused" in message:
        return "connection"

    if "empty response" in message:
        return "empty_response"

    if "invalid" in message:
        return "invalid_response"

    return "provider_error"


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------

def validate_response(response: Any) -> bool:
    """
    Verify that the provider actually returned usable inference output.

    We intentionally do NOT require the exact text "OK", because some
    providers may wrap or decorate the response.
    """

    if response is None:
        return False

    if isinstance(response, str):
        return bool(response.strip())

    if isinstance(response, dict):
        # OpenAI-style response.
        choices = response.get("choices")

        if isinstance(choices, list) and choices:
            first = choices[0]

            if isinstance(first, dict):
                message = first.get("message")

                if isinstance(message, dict):
                    content = message.get("content")

                    if isinstance(content, str) and content.strip():
                        return True

                text = first.get("text")

                if isinstance(text, str) and text.strip():
                    return True

        # Some wrappers may return content directly.
        content = response.get("content")

        if isinstance(content, str) and content.strip():
            return True

    return False


# ---------------------------------------------------------------------------
# Real model probe
# ---------------------------------------------------------------------------

def test_model(
    provider: OmniRouteProvider,
    model_id: str,
    timeout_seconds: int,
) -> HealthResult:
    """
    Perform one REAL inference request.
    """

    start = time.perf_counter()

    try:
        response = provider.generate(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a health-check model. "
                        "Respond briefly."
                    ),
                },
                {
                    "role": "user",
                    "content": HEALTH_TEST_PROMPT,
                },
            ],
            model=model_id,
            temperature=0.0,
            max_tokens=10,
            timeout_seconds=timeout_seconds,
        )

        latency_ms = int((time.perf_counter() - start) * 1000)

        if not validate_response(response):
            return HealthResult(
                model=model_id,
                status="degraded",
                latency_ms=latency_ms,
                error_type="empty_response",
                error="Model returned no usable inference content.",
            )

        return HealthResult(
            model=model_id,
            status="healthy",
            latency_ms=latency_ms,
        )

    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        error_type = classify_error(exc)

        return HealthResult(
            model=model_id,
            status="degraded",
            latency_ms=latency_ms,
            error_type=error_type,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Model discovery
# ---------------------------------------------------------------------------

def discover_models(provider: OmniRouteProvider) -> List[str]:
    """
    Discover model IDs exposed by OmniRoute.
    """

    raw_models = provider.list_models()

    model_ids: List[str] = []

    for item in raw_models:
        if isinstance(item, str):
            model_ids.append(item)
            continue

        if isinstance(item, dict):
            model_id = item.get("id")

            if model_id:
                model_ids.append(str(model_id))

    # Deduplicate while preserving order.
    seen = set()
    result = []

    for model_id in model_ids:
        if model_id not in seen:
            seen.add(model_id)
            result.append(model_id)

    return result


# ---------------------------------------------------------------------------
# Healthy model persistence
# ---------------------------------------------------------------------------

def get_health_file() -> str:
    """
    Location for machine-readable healthy model information.
    """

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    return os.path.join(
        project_root,
        "healthy_omniroute_models.json",
    )


def save_healthy_models(
    healthy_results: List[HealthResult],
    endpoint: str,
) -> str:
    """
    Save ONLY healthy models.

    Failed/degraded models are deliberately not written to the usable
    model pool.
    """

    path = get_health_file()

    payload = {
        "provider": "omniroute",
        "endpoint": endpoint,
        "verified_at": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(),
        ),
        "healthy_models": [
            {
                "model": result.model,
                "status": "healthy",
                "latency_ms": result.latency_ms,
            }
            for result in healthy_results
        ],
    }

    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print()
    print("# SOURCEAI OMNIROUTE HEALTH")
    print("=============================")
    print()

    try:
        config = LLMConfig.from_env()
    except Exception as exc:
        print(f"❌ Configuration failed: {exc}")
        return 1

    endpoint = config.omniroute_base_url
    api_key = config.omniroute_api_key

    print(f"Endpoint: {endpoint}")
    print(f"Provider: OmniRoute")
    print(f"API key loaded: {'YES' if api_key else 'NO'}")
    print(f"Healthy target: {HEALTHY_TARGET}")
    print(f"Maximum probes: {MAX_PROBES}")
    print()

    if not api_key:
        print(
            "⚠️ OMNIROUTE_API_KEY is not set. "
            "Continuing because this OmniRoute instance may allow "
            "keyless/local requests."
        )
        print()

    # ------------------------------------------------------------------
    # Initialize provider
    # ------------------------------------------------------------------

    try:
        provider = OmniRouteProvider(
            api_key=api_key,
            base_url=endpoint,
            default_timeout=config.timeout_seconds,
        )
    except Exception as exc:
        print(f"❌ Failed to initialize OmniRoute provider: {exc}")
        return 1

    # ------------------------------------------------------------------
    # Discover
    # ------------------------------------------------------------------

    try:
        discovered = discover_models(provider)
    except Exception as exc:
        print(f"❌ Model discovery failed: {exc}")
        return 1

    direct_models = [
        model
        for model in discovered
        if is_direct_model(model)
    ]

    eligible_models = [
        model
        for model in direct_models
        if is_eligible_candidate(model)
    ]

    # Ensure known priority models are tested even if discovery ordering
    # places them elsewhere.
    known_discovered = {
        model.lower(): model
        for model in discovered
    }

    ordered: List[str] = []

    for preferred in KNOWN_PRIORITY_MODELS:
        actual = known_discovered.get(preferred.lower())

        if actual and actual not in ordered:
            ordered.append(actual)

    # Add remaining candidates according to priority.
    remaining = [
        model
        for model in eligible_models
        if model not in ordered
    ]

    remaining.sort(
        key=priority_score,
        reverse=True,
    )

    ordered.extend(remaining)

    # Limit actual probing.
    candidates = ordered[:MAX_PROBES]

    print(f"Discovered models: {len(discovered)}")
    print(f"Direct models: {len(direct_models)}")
    print(f"Eligible candidates: {len(eligible_models)}")
    print(f"Models selected for probing: {len(candidates)}")
    print()

    if not candidates:
        print("❌ No eligible direct models found.")
        return 1

    print("Probing candidates with REAL inference...")
    print()

    healthy: List[HealthResult] = []

    failure_counts: Dict[str, int] = {}

    probes = 0

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------

    for model_id in candidates:
        if len(healthy) >= HEALTHY_TARGET:
            break

        probes += 1

        result = test_model(
            provider=provider,
            model_id=model_id,
            timeout_seconds=config.timeout_seconds,
        )

        if result.status == "healthy":
            healthy.append(result)

            # IMPORTANT:
            # Only healthy models are printed as usable models.
            print(
                f"🟢 {result.model} — HEALTHY — "
                f"{result.latency_ms} ms"
            )

        else:
            error_type = result.error_type or "unknown"
            failure_counts[error_type] = (
                failure_counts.get(error_type, 0) + 1
            )

            # Do NOT print every failed model.
            # This is intentionally quiet so the final output contains
            # only usable models.
            logger.debug(
                "Model %s failed: %s — %s",
                result.model,
                error_type,
                result.error,
            )

    # ------------------------------------------------------------------
    # Sort healthy models by latency
    # ------------------------------------------------------------------

    healthy.sort(
        key=lambda result: (
            result.latency_ms
            if result.latency_ms is not None
            else 10**9
        )
    )

    # ------------------------------------------------------------------
    # Save healthy model pool
    # ------------------------------------------------------------------

    health_file = save_healthy_models(
        healthy_results=healthy,
        endpoint=endpoint,
    )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    print()
    print("SUMMARY")
    print("-------")
    print(f"Discovered models: {len(discovered)}")
    print(f"Direct models: {len(direct_models)}")
    print(f"Eligible candidates: {len(eligible_models)}")
    print(f"Probed: {probes}")
    print(f"Healthy models: {len(healthy)}")
    print(f"Failed/degraded probes: {probes - len(healthy)}")
    print()

    if failure_counts:
        print("Failure categories:")
        for category, count in sorted(
            failure_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            print(f"  {category}: {count}")
        print()

    if healthy:
        print("HEALTHY MODEL POOL")
        print("------------------")

        for index, result in enumerate(healthy, start=1):
            latency = (
                f"{result.latency_ms} ms"
                if result.latency_ms is not None
                else "n/a"
            )

            print(
                f"{index}. {result.model} — {latency}"
            )

        print()
        print(f"Saved healthy model pool: {health_file}")

    else:
        print("❌ No healthy models found.")
        print()
        print(
            "No model will be marked usable because no real inference "
            "request succeeded."
        )
        print()
        print(
            "This is an actual health failure, not a fake success."
        )

        return 1

    # ------------------------------------------------------------------
    # Launch readiness
    # ------------------------------------------------------------------

    if len(healthy) < HEALTHY_TARGET:
        print()
        print(
            f"⚠️ Healthy target was {HEALTHY_TARGET}, "
            f"but only {len(healthy)} model(s) passed."
        )
        print(
            "SourceAI has at least one verified model, "
            "but redundancy is below the configured target."
        )

        # Do not fail the command if at least one real model works.
        return 0

    print()
    print(
        f"✅ OmniRoute verification passed: "
        f"{len(healthy)} healthy model(s) available."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
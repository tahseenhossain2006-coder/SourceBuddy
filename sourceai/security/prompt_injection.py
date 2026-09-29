import re
from sourceai.llm.router import ModelRouter
from sourceai.llm.tasks import LLMTask

async def detect_prompt_injection(text: str, router: ModelRouter) -> bool:
    # First, simple heuristic
    dangerous_patterns = [
        r"ignore previous instructions",
        r"reveal (?:your|the) (?:system prompt|api key|credentials)",
        r"you are now (?:a|an) (?:different|evil) assistant",
    ]
    for pat in dangerous_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    # Use Prompt Guard model if available
    try:
        response = router.route(LLMTask.PROMPT_INJECTION_DETECTION.value,
                                [{"role": "user", "content": text}],
                                max_tokens=10, temperature=0.0)
        return "malicious" in response.lower()
    except:
        return False  # conservative
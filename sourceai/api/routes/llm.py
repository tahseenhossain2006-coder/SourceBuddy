from fastapi import APIRouter
from sourceai.llm.health import check_llm_health
from sourceai.llm.config import LLMConfig

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])

@router.get("/health")
def health():
    config = LLMConfig.from_env()
    result = check_llm_health(config)
    return result
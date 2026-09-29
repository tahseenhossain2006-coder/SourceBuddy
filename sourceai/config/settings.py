# sourceai/config/settings.py
from pathlib import Path
import os

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

# settings.py
#   sourceai/config/settings.py
#
# parents[0] = sourceai/config
# parents[1] = sourceai
# parents[2] = project root
#
# Therefore the intended environment file is:
# project_root/sourceai/.env

SOURCEAI_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = SOURCEAI_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=False)


class Settings:
    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/sourceai",
    )

    # -----------------------------------------------------------------------
    # Redis
    # -----------------------------------------------------------------------

    REDIS_URL = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0",
    )

    # -----------------------------------------------------------------------
    # OpenSearch
    # -----------------------------------------------------------------------

    OPENSEARCH_HOST = os.getenv(
        "OPENSEARCH_HOST",
        "localhost",
    )

    OPENSEARCH_PORT = int(
        os.getenv("OPENSEARCH_PORT", "9200")
    )

    OPENSEARCH_USER = os.getenv(
        "OPENSEARCH_USER",
        "admin",
    )

    OPENSEARCH_PASSWORD = os.getenv(
        "OPENSEARCH_PASSWORD",
        "admin",
    )

    # -----------------------------------------------------------------------
    # LLM
    # -----------------------------------------------------------------------

    LLM_PROVIDER_ORDER = os.getenv(
        "LLM_PROVIDER_ORDER",
        "groq,openrouter,omniroute",
    )

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    GROQ_BASE_URL = os.getenv(
        "GROQ_BASE_URL",
        "https://api.groq.com/openai/v1",
    )

    GROQ_MODEL = os.getenv("GROQ_MODEL")

    GROQ_FALLBACK_MODELS = os.getenv(
        "GROQ_FALLBACK_MODELS",
        "",
    )
    AI_ENABLED = (
        os.getenv("AI_ENABLED", "false").lower() == "true"
    )

    OMNIROUTE_API_KEY = os.getenv(
        "OMNIROUTE_API_KEY"
    )

    OMNIROUTE_BASE_URL = os.getenv(
        "OMNIROUTE_BASE_URL",
        "http://localhost:20128/v1",
    )

    OMNIROUTE_MODEL = os.getenv(
        "OMNIROUTE_MODEL"
    )

    OPENROUTER_API_KEY = os.getenv(
        "OPENROUTER_API_KEY"
    )

    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1",
    )

    OPENROUTER_MODEL = os.getenv(
        "OPENROUTER_MODEL"
    )

    OPENROUTER_REASONING_ENABLED = (
        os.getenv(
            "OPENROUTER_REASONING_ENABLED",
            "false",
        ).lower()
        == "true"
    )

    LLM_TIMEOUT_SECONDS = int(
        os.getenv("LLM_TIMEOUT_SECONDS", "60")
    )

    LLM_MAX_RETRIES = int(
        os.getenv("LLM_MAX_RETRIES", "2")
    )

    # -----------------------------------------------------------------------
    # ScrapeGraphAI
    # -----------------------------------------------------------------------

    SCRAPEGRAPH_ENABLED = (
    os.getenv("SCRAPEGRAPH_ENABLED", "false").lower() == "true"
    and os.getenv("AI_ENABLED", "false").lower() == "true"
)

    SCRAPEGRAPH_PRIMARY = (
        os.getenv(
            "SCRAPEGRAPH_PRIMARY",
            "true",
        ).lower()
        == "true"
    )

    SCRAPEGRAPH_TIMEOUT_SECONDS = int(
        os.getenv(
            "SCRAPEGRAPH_TIMEOUT_SECONDS",
            "60",
        )
    )

    SCRAPEGRAPH_MAX_SUPPLIERS_PER_PAGE = int(
        os.getenv(
            "SCRAPEGRAPH_MAX_SUPPLIERS_PER_PAGE",
            "25",
        )
    )

    SCRAPEGRAPH_MAX_INPUT = int(
        os.getenv(
            "SCRAPEGRAPH_MAX_INPUT",
            str(100_000),
        )
    )

    EXTRACTION_FALLBACK_ORDER = os.getenv(
        "EXTRACTION_FALLBACK_ORDER",
        "trafilatura,bs4,readability",
    )

    # -----------------------------------------------------------------------
    # Auth
    # -----------------------------------------------------------------------

    JWT_SECRET = os.getenv(
        "JWT_SECRET",
        "change-me",
    )

    JWT_ALGORITHM = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES = 60

    # -----------------------------------------------------------------------
    # Crawl
    # -----------------------------------------------------------------------

    CRAWL_CONCURRENCY = int(
        os.getenv("CRAWL_CONCURRENCY", "5")
    )

    CRAWL_TIMEOUT = int(
        os.getenv("CRAWL_TIMEOUT", "30")
    )

    MAX_PAGE_BYTES = int(
        os.getenv(
            "MAX_PAGE_BYTES",
            str(5 * 1024 * 1024),
        )
    )

    CRAWL_USER_AGENT = os.getenv(
        "CRAWL_USER_AGENT",
        "SourceAI/1.0",
    )

    # -----------------------------------------------------------------------
    # Research budgets
    # -----------------------------------------------------------------------

    RESEARCH_MAX_ITERATIONS = int(
        os.getenv(
            "RESEARCH_MAX_ITERATIONS",
            "3",
        )
    )

    RESEARCH_MAX_WALL_TIME = int(
        os.getenv(
            "RESEARCH_MAX_WALL_TIME",
            "180",
        )
    )

    RESEARCH_MIN_SUPPLIERS = int(
        os.getenv(
            "RESEARCH_MIN_SUPPLIERS",
            "3",
        )
    )

    # -----------------------------------------------------------------------
    # SMTP
    # -----------------------------------------------------------------------

    SMTP_HOST = os.getenv("SMTP_HOST")

    SMTP_PORT = int(
        os.getenv("SMTP_PORT", "587")
    )

    SMTP_USER = os.getenv("SMTP_USER")

    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

    SMTP_FROM = os.getenv(
        "SMTP_FROM",
        "noreply@sourceai.local",
    )

    SMTP_TLS = (
        os.getenv(
            "SMTP_TLS",
            "true",
        ).lower()
        == "true"
    )
    # -----------------------------------------------------------------------
    # SearXNG (self-hosted, optional search provider)
    # -----------------------------------------------------------------------

    SEARXNG_ENABLED = (
        os.getenv("SEARXNG_ENABLED", "false").lower() == "true"
    )

    SEARXNG_BASE_URL = os.getenv(
        "SEARXNG_BASE_URL",
        "http://localhost:8080",
    )

    SEARXNG_TIMEOUT = int(
        os.getenv("SEARXNG_TIMEOUT", "15")
    )    
    # -----------------------------------------------------------------------
    # Watchlist scheduler
    # -----------------------------------------------------------------------

    WATCHLIST_CHECK_INTERVAL_MINUTES = int(
        os.getenv("WATCHLIST_CHECK_INTERVAL_MINUTES", "30")
    )

settings = Settings()
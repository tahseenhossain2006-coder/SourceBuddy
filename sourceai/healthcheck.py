# sourceai/healthcheck.py
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
print(f"GROQ_API_KEY loaded: {'YES' if os.getenv('GROQ_API_KEY') else 'NO'}")
print(f"OMNIROUTE_API_KEY loaded: {'YES' if os.getenv('OMNIROUTE_API_KEY') else 'NO'}")

from sourceai.search.router import SearchRouter
from sourceai.llm.verify_all_models import main as llm_verify
from sourceai.storage.postgres import PostgresStorage
from sourceai.storage.redis import RedisCache
from sourceai.storage.opensearch import OpenSearchIndexer


async def healthcheck():
    print("SOURCEAI HEALTH CHECK")
    print("=====================")

    # Diagnostic: show key status
    print(f"GROQ_API_KEY loaded: {'YES' if os.getenv('GROQ_API_KEY') else 'NO'}")
    print(f"OMNIROUTE_API_KEY loaded: {'YES' if os.getenv('OMNIROUTE_API_KEY') else 'NO'}")
    print()

    # ---------- Search Engines ----------
    router = SearchRouter()
    engines = ["YaCy", "DuckDuckGo", "Google", "Bing"]
    tasks = [engine.health_check() for engine in router.engines]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, res in enumerate(results):
        status = "HEALTHY" if res else "DEGRADED"
        print(f"{engines[i]}: {status}")

    # ---------- LLM Models ----------
    print("\nLLM Models:")
    # The verify_all_models function prints its own output
    llm_verify()

    # ---------- Storage ----------
    print("\nStorage:")
    # PostgreSQL
    pg = PostgresStorage()
    try:
        await pg.connect()
        print("PostgreSQL: HEALTHY")
    except Exception as e:
        print(f"PostgreSQL: UNHEALTHY ({e})")

    # Redis
    redis = RedisCache()
    try:
        await redis.connect()
        # Test set/get
        await redis.set("healthcheck:test", {"status": "ok"}, ttl=10)
        val = await redis.get("healthcheck:test")
        if val and val.get("status") == "ok":
            print("Redis: HEALTHY")
        else:
            print("Redis: DEGRADED")
    except Exception as e:
        print(f"Redis: UNHEALTHY ({e})")

    # OpenSearch
    osi = OpenSearchIndexer()
    try:
        osi.connect()
        # Simple info call
        info = osi.client.info()
        if info.get("version"):
            print("OpenSearch: HEALTHY")
        else:
            print("OpenSearch: DEGRADED")
    except Exception as e:
        print(f"OpenSearch: UNHEALTHY ({e})")

    print("\n✅ Health check complete.")


if __name__ == "__main__":
    asyncio.run(healthcheck())
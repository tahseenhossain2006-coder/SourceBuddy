import asyncio
from sourceai.search.engines.bing import BingEngine

async def main():
    engine = BingEngine()
    results = await engine.search("BLDC motor manufacturer India", limit=5)
    print("results:", len(results))
    for i, r in enumerate(results, 1):
        marker = "WRAPPED" if "bing.com/ck/a" in r.url else "OK"
        print(f"  [{i}] {marker}  {r.url}")

asyncio.run(main())

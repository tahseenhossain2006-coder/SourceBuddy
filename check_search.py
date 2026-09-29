# check_search.py
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)

    searches = await conn.fetch(
        "SELECT id, user_id, query, status, created_at FROM searches ORDER BY created_at DESC LIMIT 5"
    )
    print(f"Searches stored: {len(searches)}")
    for s in searches:
        print(f"  {s['id']} | {s['status']} | {s['query'][:60]}")

    suppliers = await conn.fetch(
        "SELECT id, company_name, country, moq, website FROM suppliers LIMIT 10"
    )
    print(f"\nSuppliers stored: {len(suppliers)}")
    for s in suppliers:
        print(f"  {s['company_name']} | {s['country']} | MOQ={s['moq']} | {s['website']}")

    await conn.close()


asyncio.run(main())
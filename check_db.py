import asyncio
from sourceai.storage.postgres import PostgresStorage

async def main():
    s = PostgresStorage()
    await s.connect()
    row = await s.pool.fetchrow("SELECT 1 AS ok")
    print("DB OK:", row["ok"])

    for table in ("searches", "suppliers", "users"):
        rows = await s.pool.fetch(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
            """,
            table,
        )
        print(f"--- {table} ---")
        if not rows:
            print("  (table does not exist)")
        for r in rows:
            print(f"  {r['column_name']:25} {r['data_type']:20} nullable={r['is_nullable']}")
    await s.close()

asyncio.run(main())

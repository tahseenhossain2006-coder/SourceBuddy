# sourceai/api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging

from sourceai.auth.dependencies import get_current_user
from sourceai.search.agent import SearchAgent
from sourceai.llm.router import ModelRouter
from sourceai.llm.config import LLMConfig
from sourceai.llm.provider_factory import get_all_providers
from sourceai.usage.service import UsageService
from sourceai.storage.postgres import PostgresStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])
usage = UsageService()

config = LLMConfig.from_env()
providers = get_all_providers(config)
llm_router = ModelRouter(config, providers)
agent = SearchAgent(llm_router)
db = PostgresStorage()


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
async def search(req: SearchRequest, user_id: str = Depends(get_current_user)):
    if not await usage.check_and_reserve(user_id, "search"):
        raise HTTPException(status_code=429, detail="Daily search limit reached")

    try:
        result = await agent.search(req.query, user_id=user_id)
    except Exception:
        # Log full traceback server-side; never expose it to the client.
        logger.exception("Search failed for user=%s", user_id)
        raise HTTPException(status_code=500, detail="Search failed")

    return {"status": "success", "data": result}


@router.get("/search/{search_id}")
async def get_search(search_id: str, user_id: str = Depends(get_current_user)):
    """
    Fetch a previously persisted search by its DB id.

    The id returned by POST /search is the PostgreSQL primary key.
    Ownership is enforced: only the user who created the search can read it.
    """
    try:
        await db.connect()
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, query, search_plan, status,
                       created_at, updated_at
                FROM searches
                WHERE id = $1
                """,
                _coerce_search_id(search_id),
            )
    except ValueError:
        # Bad UUID format in path
        raise HTTPException(status_code=400, detail="Invalid search id")
    except Exception:
        logger.exception("DB error loading search id=%s", search_id)
        raise HTTPException(status_code=503, detail="Search backend unavailable")

    if row is None:
        raise HTTPException(status_code=404, detail="Search not found")
    if str(row["user_id"]) != str(user_id):
        # Do not leak existence of other users' searches
        raise HTTPException(status_code=404, detail="Search not found")

    suppliers = []
    try:
        async with db.pool.acquire() as conn:
            sup_rows = await conn.fetch(
                """
                SELECT company_name, website, country, location,
                       moq, price, currency, metadata, created_at
                FROM suppliers
                WHERE search_id = $1
                ORDER BY created_at ASC
                """,
                row["id"],
            )
        for s in sup_rows:
            suppliers.append(
                {
                    "company_name": s["company_name"],
                    "website": s["website"],
                    "country": s["country"],
                    "location": s["location"],
                    "moq": s["moq"],
                    "price": s["price"],
                    "currency": s["currency"],
                    "evidence": s["metadata"],
                    "created_at": s["created_at"].isoformat()
                    if s["created_at"]
                    else None,
                }
            )
    except Exception:
        logger.exception("DB error loading suppliers for search id=%s", row["id"])

    return {
        "status": "success",
        "data": {
            "search_id": str(row["id"]),
            "query": row["query"],
            "plan": row["search_plan"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat()
            if row["created_at"]
            else None,
            "updated_at": row["updated_at"].isoformat()
            if row["updated_at"]
            else None,
            "suppliers": suppliers,
        },
    }


@router.get("/health")
async def health():
    return {"status": "ok"}


# --------------------------------------------------------------------- helpers
def _coerce_search_id(value: str):
    """
    The searches.id column is assumed to be UUID-typed.
    If it is TEXT, this still works — just returns the string unchanged.
    """
    from uuid import UUID

    try:
        return UUID(value)
    except (ValueError, TypeError, AttributeError):
        return value
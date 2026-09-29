# sourceai/tests/test_search_agent.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sourceai.search.agent import SearchAgent
from sourceai.search.planner import SearchPlan
from sourceai.llm.router import ModelRouter
from sourceai.llm.config import LLMConfig


@pytest.fixture
def mock_router():
    """Create a mock ModelRouter that returns predefined responses."""
    router = MagicMock(spec=ModelRouter)
    router.route = AsyncMock(return_value='{"product":"t-shirt","quantity":500}')
    return router


@pytest.fixture
def agent(mock_router):
    """Create a SearchAgent instance with a mock router."""
    config = LLMConfig.from_env()
    return SearchAgent(llm_router=mock_router)


@pytest.mark.asyncio
async def test_search_agent_instantiation(agent):
    """Test that the agent can be instantiated."""
    assert agent is not None
    assert agent.planner is not None
    assert agent.router is not None
    assert agent.crawler is not None
    assert agent.extractor is not None
    assert agent.llm is not None
    assert agent.db is not None
    assert agent.indexer is not None


@pytest.mark.asyncio
async def test_agent_search_plan_creation(agent):
    """Test that the agent can create a SearchPlan from a query."""
    plan = agent.planner.plan("Find cotton t-shirt manufacturers in India")
    assert plan is not None
    assert isinstance(plan, SearchPlan)
    assert "cotton" in plan.original_query.lower()
    assert len(plan.expanded_queries) > 0


@pytest.mark.asyncio
@patch("sourceai.search.router.SearchRouter.search", new_callable=AsyncMock)
@patch("sourceai.crawling.manager.CrawlManager.crawl", new_callable=AsyncMock)
@patch("sourceai.extraction.pipeline.ExtractionPipeline.extract")
@patch("sourceai.llm.integration.LLMIntegration.extract_suppliers", new_callable=MagicMock)
@patch("sourceai.llm.integration.LLMIntegration.rank_suppliers", new_callable=MagicMock)
@patch("sourceai.llm.integration.LLMIntegration.generate_final_answer", new_callable=MagicMock)
async def test_agent_full_search(
    mock_final_answer,
    mock_rank,
    mock_extract_suppliers,
    mock_extract,
    mock_crawl,
    mock_search,
    agent,
):
    """Test the full search pipeline with mocks to avoid external calls."""

    # Mock search results
    mock_search.return_value = [
        MagicMock(url="https://example.com/supplier1", title="Supplier A", snippet="Cotton t-shirts", source_engine="ddg")
    ]

    # Mock crawl results
    mock_crawl.return_value = [{"url": "https://example.com/supplier1", "html": "<html>...</html>", "status": 200}]

    # Mock extraction
    mock_extract.return_value = [{"url": "https://example.com/supplier1", "title": "Supplier A", "text": "MOQ 500 pieces"}]

    # Mock supplier extraction – return a dict, not a MagicMock
    supplier_dict = {
        "supplier_name": "ABC Garments",
        "company_name": "ABC Garments Pvt Ltd",
        "country": "India",
        "moq": 300,
        "price": None,
        "currency": "INR",
        "website": "https://example.com",
        "evidence": {"moq": {"value": 300, "source": "page"}},
        "confidence": 0.8,
        "supplier_type": "manufacturer",
    }
    mock_extract_suppliers.return_value = [supplier_dict]

    # Mock ranking – return the same dicts (ranked)
    mock_rank.return_value = [supplier_dict]

    # Mock final answer
    mock_final_answer.return_value = "Found 1 supplier: ABC Garments."

    # Execute search
    result = await agent.search("Find 5 t-shirt manufacturers in India with MOQ below 500")

    assert result is not None
    assert "search_id" in result
    assert "suppliers" in result
    assert len(result["suppliers"]) > 0
    assert result["suppliers"][0]["supplier_name"] == "ABC Garments"
    assert "answer" in result
    assert "evidence" in result


@pytest.mark.asyncio
async def test_agent_deduplication(agent):
    """Test the internal deduplication method."""
    from sourceai.search.engines.base import SearchResult

    results = [
        SearchResult(title="A", url="https://example.com/1", snippet="test", source_engine="ddg", query="test"),
        SearchResult(title="B", url="https://example.com/1", snippet="dup", source_engine="google", query="test"),
        SearchResult(title="C", url="https://example.com/2", snippet="unique", source_engine="ddg", query="test"),
    ]
    deduped = agent._deduplicate(results)
    assert len(deduped) == 2
    assert deduped[0].url == "https://example.com/1"  # first occurrence kept
    assert deduped[1].url == "https://example.com/2"


@pytest.mark.asyncio
async def test_agent_ranking(agent):
    """Test the internal ranking method."""
    from sourceai.search.engines.base import SearchResult

    plan = agent.planner.plan("Find t-shirts")
    results = [
        SearchResult(title="Cotton T-Shirt Supplier", url="https://a.com", snippet="best cotton", source_engine="google", query="t-shirts"),
        SearchResult(title="Polyester T-Shirt", url="https://b.com", snippet="cheap", source_engine="ddg", query="t-shirts"),
    ]
    ranked = agent._rank(results, plan)
    # The first result should have higher score because it matches keywords better
    assert ranked[0].title == "Cotton T-Shirt Supplier"


@pytest.mark.asyncio
async def test_agent_apply_filters(agent):
    """Test that filters are applied correctly."""
    plan = agent.planner.plan("Find t-shirts with MOQ below 500")
    plan.constraints = {"max_moq": 500, "location": "India"}

    # Use real dicts, not MagicMock, because _apply_filters uses s["moq"] and s.get()
    suppliers = [
        {"moq": 300, "country": "India", "supplier_type": "manufacturer"},
        {"moq": 600, "country": "India", "supplier_type": "manufacturer"},
        {"moq": 400, "country": "China", "supplier_type": "manufacturer"},
    ]
    filtered = agent._apply_filters(suppliers, plan)
    assert len(filtered) == 1
    assert filtered[0]["moq"] == 300
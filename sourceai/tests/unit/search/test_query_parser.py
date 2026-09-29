"""Deterministic query parser tests."""
import pytest

from sourceai.search.planner import SearchPlanner


@pytest.fixture
def planner():
    return SearchPlanner()


# ---------------------------------------------------------------------------
# MOQ extraction
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,expected_moq", [
    ("stainless steel bottle supplier India MOQ 500", 500),
    ("bottle supplier MOQ: 100", 100),
    ("bottle supplier MOQ 1,000", 1000),
    ("bottle supplier minimum order 500 pieces", 500),
    ("bottle supplier minimum order quantity 250", 250),
])
def test_moq_extraction(planner, query, expected_moq):
    plan = planner.plan(query)
    assert plan.constraints.get("max_moq") == expected_moq, (
        f"query={query!r} constraints={plan.constraints}"
    )


# ---------------------------------------------------------------------------
# Currency and price
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,expected_price,expected_currency", [
    ("industrial LED light under $5", 5, "USD"),
    ("bottle under 200 INR", 200, "INR"),
    ("bottle max 10 USD", 10, "USD"),
    ("bottle budget 15 GBP", 15, "GBP"),
])
def test_price_and_currency(planner, query, expected_price, expected_currency):
    plan = planner.plan(query)
    assert plan.constraints.get("max_price") == expected_price, (
        f"query={query!r} constraints={plan.constraints}"
    )
    assert plan.entities.get("currency") == expected_currency or \
           plan.constraints.get("currency") == expected_currency


# ---------------------------------------------------------------------------
# Country / location
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,expected_country", [
    ("stainless steel bottle supplier India MOQ 500", "India"),
    ("cotton t-shirt manufacturer Bangladesh", "Bangladesh"),
    ("industrial LED light manufacturer China", "China"),
    ("aluminium bottle supplier Vietnam", "Vietnam"),
])
def test_country_extraction(planner, query, expected_country):
    plan = planner.plan(query)
    assert plan.entities.get("country") == expected_country, (
        f"query={query!r} entities={plan.entities}"
    )


# ---------------------------------------------------------------------------
# Supplier type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,expected_type", [
    ("stainless steel bottle manufacturer India", "manufacturer"),
    ("bottle supplier India", "supplier"),
    ("bottle wholesaler India", "wholesaler"),
    ("bottle distributor India", "distributor"),
])
def test_supplier_type(planner, query, expected_type):
    plan = planner.plan(query)
    assert plan.entities.get("supplier_type") == expected_type, (
        f"query={query!r} entities={plan.entities}"
    )


# ---------------------------------------------------------------------------
# Product extraction
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,expected_substring", [
    ("stainless steel bottle supplier India MOQ 500", "stainless steel bottle"),
    ("1000 pcs cotton t-shirt manufacturer Bangladesh", "cotton t-shirt"),
    ("industrial LED light India under $5", "LED light"),
])
def test_product_extraction(planner, query, expected_substring):
    plan = planner.plan(query)
    product = (plan.entities.get("product") or "").lower()
    assert expected_substring.lower() in product, (
        f"query={query!r} product={product!r}"
    )


# ---------------------------------------------------------------------------
# Combined / full parse
# ---------------------------------------------------------------------------

def test_full_parse_stainless_steel(planner):
    plan = planner.plan("stainless steel bottle supplier India MOQ 500")
    assert "stainless steel bottle" in (plan.entities.get("product") or "").lower()
    assert plan.entities.get("supplier_type") == "supplier"
    assert plan.entities.get("country") == "India"
    assert plan.constraints.get("max_moq") == 500


def test_full_parse_cotton_tshirt(planner):
    plan = planner.plan("1000 pcs cotton t-shirt manufacturer Bangladesh")
    assert "cotton" in (plan.entities.get("product") or "").lower()
    assert plan.entities.get("supplier_type") == "manufacturer"
    assert plan.entities.get("country") == "Bangladesh"


def test_full_parse_led(planner):
    plan = planner.plan("industrial LED light India under $5")
    assert "LED" in (plan.entities.get("product") or "")
    assert plan.constraints.get("max_price") == 5


# ---------------------------------------------------------------------------
# No false positives
# ---------------------------------------------------------------------------

def test_no_invented_moq(planner):
    plan = planner.plan("stainless steel bottle supplier India")
    assert plan.constraints.get("max_moq") is None


def test_no_invented_country(planner):
    plan = planner.plan("stainless steel bottle supplier")
    assert plan.entities.get("country") is None


def test_no_invented_price(planner):
    plan = planner.plan("stainless steel bottle supplier India")
    assert plan.constraints.get("max_price") is None


# ---------------------------------------------------------------------------
# Expansion
# ---------------------------------------------------------------------------

def test_expanded_queries_include_original(planner):
    plan = planner.plan("stainless steel bottle supplier India MOQ 500")
    assert plan.expanded_queries[0] == "stainless steel bottle supplier India MOQ 500"


def test_expanded_queries_are_bounded(planner):
    plan = planner.plan("stainless steel bottle supplier India MOQ 500")
    assert len(plan.expanded_queries) <= 8


def test_expanded_queries_have_no_duplicates(planner):
    plan = planner.plan("stainless steel bottle supplier India MOQ 500")
    assert len(plan.expanded_queries) == len(set(plan.expanded_queries))


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------

def test_keywords_drop_stopwords(planner):
    plan = planner.plan("find stainless steel bottle in India")
    assert "find" not in plan.keywords
    assert "in" not in plan.keywords
    assert "stainless" in plan.keywords
    assert "bottle" in plan.keywords

# ---------------------------------------------------------------------------
# Quantity extraction
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,expected_qty", [
    ("1000 pcs cotton t-shirt manufacturer Bangladesh", 1000),
    ("5K pieces of stainless steel bottle", 5000),
    ("need 5000 units of aluminium bottle", 5000),
    ("10 cartons of LED lights", 10),
])
def test_quantity_extraction(planner, query, expected_qty):
    plan = planner.plan(query)
    assert plan.entities.get("quantity") == expected_qty, (
        f"query={query!r} entities={plan.entities}"
    )


def test_product_does_not_include_quantity(planner):
    """Product must not contain leading numbers or unit words."""
    plan = planner.plan("1000 pcs cotton t-shirt manufacturer Bangladesh")
    product = (plan.entities.get("product") or "").lower()
    assert "1000" not in product
    assert "pcs" not in product
    assert "cotton" in product
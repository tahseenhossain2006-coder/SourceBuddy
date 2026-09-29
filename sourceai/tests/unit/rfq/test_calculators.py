"""Procurement calculator tests."""
import pytest

from sourceai.rfq.calculators import (
    unit_times_quantity,
    moq_feasibility,
    budget_feasibility,
    total_quoted_cost,
    price_per_unit,
    quantity_difference,
)


# ---------------------------------------------------------------------------
# unit_times_quantity
# ---------------------------------------------------------------------------

def test_unit_times_quantity_basic():
    r = unit_times_quantity(2.50, 1000)
    assert r["value"] == 2500.00
    assert r["currency"] == "USD"


def test_unit_times_quantity_zero_qty():
    r = unit_times_quantity(2.50, 0)
    assert r["value"] == 0.0


def test_unit_times_quantity_negative_rejected():
    r = unit_times_quantity(-1, 10)
    assert r["value"] is None


def test_unit_times_quantity_parses_string_price():
    r = unit_times_quantity("2,500.00", 2, currency="INR")
    assert r["value"] == 5000.00


# ---------------------------------------------------------------------------
# moq_feasibility
# ---------------------------------------------------------------------------

def test_moq_feasible():
    r = moq_feasibility(1000, 500)
    assert r["feasible"] is True
    assert r["value"] == 0


def test_moq_short_by_n():
    r = moq_feasibility(300, 500)
    assert r["feasible"] is False
    assert r["value"] == 200


def test_moq_zero_constraint():
    r = moq_feasibility(100, 0)
    assert r["feasible"] is True
    assert r["value"] == 0


# ---------------------------------------------------------------------------
# budget_feasibility
# ---------------------------------------------------------------------------

def test_budget_within():
    r = budget_feasibility(2.0, 100, 500)
    assert r["feasible"] is True
    assert r["value"] == 0


def test_budget_over():
    r = budget_feasibility(10.0, 100, 500)
    assert r["feasible"] is False
    assert r["value"] == 500.00


def test_budget_exact():
    r = budget_feasibility(5.0, 100, 500)
    assert r["feasible"] is True


# ---------------------------------------------------------------------------
# total_quoted_cost
# ---------------------------------------------------------------------------

def test_total_quoted_cost_with_shipping():
    r = total_quoted_cost(2.5, 1000, shipping=250.0, currency="USD")
    assert r["value"] == 2750.0


def test_total_quoted_cost_no_shipping():
    r = total_quoted_cost(2.5, 1000)
    assert r["value"] == 2500.0


# ---------------------------------------------------------------------------
# price_per_unit
# ---------------------------------------------------------------------------

def test_price_per_unit_basic():
    r = price_per_unit(2500.0, 1000)
    assert r["value"] == 2.5


def test_price_per_unit_zero_quantity():
    r = price_per_unit(2500.0, 0)
    assert r["value"] is None


# ---------------------------------------------------------------------------
# quantity_difference
# ---------------------------------------------------------------------------

def test_quantity_difference_positive():
    r = quantity_difference(500, 800)
    assert r["value"] == 300


def test_quantity_difference_negative():
    r = quantity_difference(1000, 700)
    assert r["value"] == -300


def test_quantity_difference_exact():
    r = quantity_difference(500, 500)
    assert r["value"] == 0
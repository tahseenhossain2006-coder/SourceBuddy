import json
from unittest.mock import MagicMock, patch

import pytest

from sourceai.extraction import scrapegraph as sg_mod
from sourceai.extraction.scrapegraph import ScrapeGraphExtractor


def test_import_target_is_2x_symbol():
    # If scrapegraphai 2.2.4 is installed, the correct symbol must import.
    assert sg_mod.SG_AVAILABLE is True, (
        f"ScrapeGraphAI import failed: {sg_mod.SG_IMPORT_ERROR!r}"
    )
    assert sg_mod.SmartScraperGraph is not None


def test_returns_none_when_disabled(monkeypatch):
    monkeypatch.setenv("SCRAPEGRAPH_ENABLED", "false")
    ex = ScrapeGraphExtractor()
    assert ex.extract("<html></html>", "https://x") is None


def test_returns_none_on_import_failure(monkeypatch):
    monkeypatch.setattr(sg_mod, "SG_AVAILABLE", False)
    monkeypatch.setattr(sg_mod, "SmartScraperGraph", None)
    ex = ScrapeGraphExtractor()
    assert ex.extract("<html></html>", "https://x") is None


def test_returns_none_when_no_llm_config(monkeypatch):
    monkeypatch.setenv("SCRAPEGRAPH_ENABLED", "true")

    # Clear env vars
    for k in ("GROQ_API_KEY", "OPENROUTER_API_KEY",
              "GROQ_MODEL", "OPENROUTER_MODEL"):
        monkeypatch.delenv(k, raising=False)

    # Also clear the settings-backed values, since _llm_config() reads
    # from settings as a fallback when the env var is absent.
    from sourceai.config import settings as settings_module
    monkeypatch.setattr(settings_module.settings, "GROQ_API_KEY", None)
    monkeypatch.setattr(settings_module.settings, "GROQ_MODEL", None)
    monkeypatch.setattr(settings_module.settings, "OPENROUTER_API_KEY", None)
    monkeypatch.setattr(settings_module.settings, "OPENROUTER_MODEL", None)

    ex = ScrapeGraphExtractor()
    ex._provider_order = []          # force empty loop
    assert ex.extract("<html></html>", "https://x") is None


def test_successful_extraction_with_mocked_graph(monkeypatch):
    monkeypatch.setenv("SCRAPEGRAPH_ENABLED", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.delenv("REDIS_URL", raising=False)

    fake_result = {
        "suppliers": [
            {"company_name": "Acme Metals", "country": "IN",
             "products": ["enclosures"]}
        ],
        "evidence": [{"field": "company_name", "value": "Acme Metals",
                      "evidence": "Acme Metals Pvt Ltd"}],
    }

    fake_graph = MagicMock()
    fake_graph.run.return_value = json.dumps(fake_result)

    with patch.object(sg_mod, "SmartScraperGraph", return_value=fake_graph):
        ex = ScrapeGraphExtractor()
        out = ex.extract("<html>Acme Metals Pvt Ltd</html>",
                         "https://acme.example")

    assert out is not None
    assert out["suppliers"][0]["company_name"] == "Acme Metals"
    assert out["source_url"] == "https://acme.example"


def test_qwen_model_is_rejected_for_groq(monkeypatch):
    monkeypatch.setenv("SCRAPEGRAPH_ENABLED", "true")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setenv("GROQ_MODEL", "qwen/qwen3-27b")
    ex = ScrapeGraphExtractor()
    ex._provider_order = ["groq"]
    assert ex._llm_config() is None


def test_graph_exception_returns_none_not_raises(monkeypatch):
    monkeypatch.setenv("SCRAPEGRAPH_ENABLED", "true")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    failing = MagicMock()
    failing.run.side_effect = RuntimeError("upstream 500")

    with patch.object(sg_mod, "SmartScraperGraph", return_value=failing):
        ex = ScrapeGraphExtractor()
        out = ex.extract("<html></html>", "https://x")

    assert out is None    # degrade, don't raise, don't fabricate
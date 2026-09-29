# SourceAI

Autonomous supplier discovery and procurement intelligence backend.

SourceAI takes a natural-language sourcing query, runs it through a
multi-provider search layer, crawls the resulting pages, extracts
structured supplier records, and returns ranked, evidence-backed
results via a REST API.

The V1 launch runs entirely **without an LLM**. An AI upgrade path is
already wired (see `ARCHITECTURE.md`) and can be enabled by flipping one
environment variable.

## What it does

- **Multi-provider search**: DuckDuckGo, SearXNG (self-hosted), YaCy,
  Whoogle, Bing — with automatic failover
- **Deterministic query understanding**: extracts product, quantity,
  MOQ, price, currency, country, supplier type, and certifications
- **Crawling with SSRF protection**: rejects private IPs, cloud
  metadata endpoints, non-HTTP schemes, oversized responses, and
  redirect-to-private
- **Supplier extraction**: regex + dictionary based, with per-field
  evidence, deterministic confidence, and data completeness
- **Cross-source normalization**: merges duplicate suppliers by domain,
  email domain, or normalized name
- **Contradiction detection**: flags mismatched MOQ / price / location
  across sources
- **Watchlists and alerts**: hash-based change detection
- **RFQ / outreach / quotes**: deterministic templates, procurement
  calculators, currency normalization
- **PostgreSQL persistence** with Alembic migrations
- **Docker Compose** full stack: API + Postgres + Redis + SearXNG

## What it does not do

- No LLM-generated natural-language answers in V1
- No paid search APIs (Brave, SerpAPI, Tavily)
- No automated procurement decisions
- No frontend (backend only)

## Quick start

### Docker (recommended)

```bash
git clone <repo> sourceai
cd sourceai
cp .env.example .env
docker compose up -d postgres redis
docker compose up -d api
docker compose exec api alembic upgrade head
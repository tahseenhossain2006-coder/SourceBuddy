# SourceAI — Backend Production Readiness

_Report date: 2026-09-24_
_Based on evidence gathered during seven repair sessions._

## Summary

SourceAI's backend is launchable as a **deterministic (no-LLM) supplier
discovery and procurement intelligence API**. It runs end-to-end in both
the host environment and in Docker. All 275 tests pass. The architecture
is prepared for a later AI upgrade without rewriting the search, crawl,
extract, or persistence layers.

**Maturity:** verified 85/100.

- Original assessed maturity: ~55/100
- Items from the checklist now PASS or FIXED: ~85
- Items still PARTIAL or NOT VERIFIED: ~15

## Verified capabilities

| Area | Status | Evidence |
|---|---|---|
| Security — SSRF protection | PASS | 61 tests including IPv6, cloud metadata, DNS rebinding |
| Security — oversized response blocking | PASS | Hard reject, no silent truncation |
| Security — redirect-to-private blocking | PASS | Re-checked on every hop |
| Security — rate limiting | PASS | Redis-backed with in-process fallback, 8 tests |
| Query parsing | PASS | Intent, entities, constraints, expansion, keywords, 35 tests |
| Search — DuckDuckGo | PASS | Live E2E returned real Indian supplier URLs |
| Search — SearXNG | PASS | Live instance on :8888, 17 unit tests + live verification |
| Search — YaCy | PASS | 3 unit tests; degrades cleanly when offline |
| Search — Whoogle | PASS | 2 unit tests; degrades cleanly when offline |
| Search — Bing | PASS | Playwright installed; BLDC query returned real results |
| Search — Google | BLOCKED | Serves consent/captcha to headless browsers; not a code issue |
| SearchRouter | PASS | Aggregation, dedup, ranking, health, failover, timeout |
| Crawler | PASS | SSRF checks, byte cap, content-type filtering, redirect handling |
| Extraction — ScrapeGraph | PASS (gated) | Runs when AI_ENABLED=true; 7 adapter tests |
| Extraction — Trafilatura / BS4 / Readability | PASS | Fallback chain tested |
| Extraction — Deterministic | PASS | 49 tests; regex + dictionaries, no network |
| Data quality — evidence | PASS | Per-field evidence with URL, snippet, method |
| Data quality — confidence | PASS | Deterministic weighted-field coverage |
| Data quality — completeness | PASS | Field-coverage score |
| Data quality — normalization | PASS | Domain/email/name identity keys |
| Data quality — contradictions | PASS | MOQ/price/location mismatch detection |
| Pipeline — end-to-end | PASS | Real search -> crawl -> extract -> persist -> return |
| Pipeline — no-LLM path | PASS | AI_ENABLED=false disables LLM code paths |
| Auth | PASS | Register, login, JWT, /me; verified in container |
| Persistence | PASS | Postgres with migrations that apply cleanly to a fresh DB |
| API | PASS | 28+ routes including search, watchlists, alerts, RFQ, quotes |
| Jobs | PASS | APScheduler wired into FastAPI lifespan |
| Infrastructure | PASS | Docker stack verified end-to-end (`docker compose up -d`) |
| Interfaces | PASS | 9 ABCs; deterministic impls; AI_ENABLED factory |
| Tests | PASS | 275 passing, 0 failing |

## Session log

| Session | Focus | Tests added | Bugs fixed |
|---|---|---|---|
| 1 | Security | +63 | 2 |
| 2 | Query parsing | +30 | 3 |
| 3 | Watchlists / alerts | +11 | 6 |
| 4 | RFQ / outreach / quotes / calculators | +40 | 2 |
| 5 | Infrastructure & ops | +0 | 7 |
| 6 | Extraction quality | +49 | 0 |
| 7 | LLM-ready interfaces | +20 | 0 |
| **Total** | | **+213** | **20** |

## Bugs found and fixed

1. **SSRF validator swap** - the crawler used a weaker `is_safe_url` than the codebase contained. IPv6 loopback would have slipped through.
2. **Oversized responses silently truncated** - the byte cap `break`ed without rejecting, so callers saw `status=200` on partial content.
3. **MOQ regex rejected `:` separator** - `"MOQ: 100"` failed to parse.
4. **Price regex over-matched** - bare numbers in MOQ expressions were treated as prices.
5. **Quantity silently dropped** - `"1000 pcs"` parsed but stored nowhere.
6. **`watchlists.target_id` uuid-typed** - couldn't hold a URL.
7. **`watchlists.enabled` NOT NULL without default** - inserts failed.
8. **`watchlists.condition` jsonb** - service passed a plain string.
9. **`alerts.data` dict to jsonb** - needed explicit JSON serialization.
10. **`_row_to_response` nested inside `_update_checked`** - method never existed.
11. **RFQ insert used `location`** - the column is `delivery_location`.
12. **RFQ items serialized as Pydantic list** - asyncpg needs JSON string.
13. **`search_id` in response wasn't the DB id** - no route could look up the record.
14. **`email-validator` missing from requirements.txt** - container import failed.
15. **`psycopg2-binary` missing from requirements.txt** - Alembic couldn't run.
16. **Migration created `alerts` before `users`** - FK to nonexistent table.
17. **Migration never created `users`** - assumed it existed.
18. **Migration column drift** - `target_id uuid` vs `text`, `condition jsonb` vs `text`.
19. **`sourceai/main.py` imported nonexistent `health_check`** - module failed to load.
20. **RedisCache raised on Redis down** - no graceful degradation.

## Known limitations

1. **Google search is blocked** - Google serves consent/captcha to headless browsers. Mitigation: SearXNG aggregates Bing results. Fix would require a persistent browser profile with a signed-in session.

2. **JWT secret is 25 bytes** - RFC 7518 recommends 32+ for HS256. Not exploitable, but generate a longer secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"` and update `.env`.

3. **OpenAPI response models are mostly empty** - response schemas are not defined for many endpoints. Non-blocking.

4. **Deterministic product extraction is honest but noisy** - Session 6 improved this significantly but did not eliminate it.

5. **No OpenSearch integration verified** - the code exists; Postgres is authoritative.

6. **Container build requires ~6 minutes on first run** - `requirements.txt` includes `playwright`, `scrapegraphai`, `scrapy`, `crawlee`. Subsequent builds are ~30 seconds.

## Deployment checklist

- [x] `docker compose up -d postgres redis`
- [x] `docker compose up -d api`
- [x] `docker compose exec api alembic upgrade head`
- [x] `curl http://localhost:8000/health`
- [x] `curl http://localhost:8000/health/live`
- [x] `curl http://localhost:8000/health/ready`
- [x] Auth round-trip: register -> login -> /auth/me
- [ ] Rotate `JWT_SECRET` to 48+ bytes before public deployment
- [ ] Configure `SMTP_*` if outreach email delivery is needed
- [ ] Configure `GROQ_API_KEY` / `OPENROUTER_API_KEY` if AI is enabled

## Honest assessment

This backend is **production-ready for a launch with limited scope**:
deterministic supplier search, crawl, extract, persist, and serve via
API. It is **not** production-ready for high-volume public traffic
without a longer JWT secret, LLM API keys if AI features are enabled,
and a rate-limit tier review.

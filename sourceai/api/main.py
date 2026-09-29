# sourceai/api/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sourceai.observability.logging import setup_logging
from sourceai.security.headers import SecurityHeadersMiddleware

from sourceai.api.routes import router as api_router
from sourceai.auth.router import router as auth_router
from sourceai.rfq.routes import router as rfq_router
from sourceai.outreach.routes import router as outreach_router
from sourceai.watchlists.routes import router as watchlists_router
from sourceai.alerts.routes import router as alerts_router
from sourceai.admin.routes import router as admin_router
from sourceai.watchlists.scheduler import start_scheduler
from sourceai.api.middleware import rate_limit_middleware


logger = logging.getLogger(__name__)

setup_logging()

_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler

    # Startup validation — logs, does not abort on optional dependency failure
    try:
        from sourceai.main import validate_startup
        await validate_startup()
    except Exception:
        logger.exception("Startup validation failed (non-fatal)")

    # Background scheduler
    try:
        _scheduler = start_scheduler()
    except Exception:
        logger.exception(
            "Failed to start watchlist scheduler; continuing without it"
        )
        _scheduler = None

    try:
        yield
    finally:
        if _scheduler is not None:
            try:
                _scheduler.shutdown(wait=False)
            except Exception:
                logger.exception("Scheduler shutdown failed")
        logger.exception(
            "Failed to start watchlist scheduler; continuing without it"
        )
        _scheduler = None

    try:
        yield
    finally:
        if _scheduler is not None:
            try:
                _scheduler.shutdown(wait=False)
            except Exception:
                logger.exception("Scheduler shutdown failed")


app = FastAPI(title="SourceAI", version="1.0.0", lifespan=lifespan)

app.add_middleware(SecurityHeadersMiddleware)
from sourceai.api.middleware import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(rate_limit_middleware)

# NOTE: Each router declares its own prefix internally.
# Do NOT add prefix= here for routers that already declare one.
app.include_router(auth_router,       tags=["auth"])
app.include_router(api_router,        tags=["search"])
app.include_router(rfq_router,        tags=["rfq"])
app.include_router(outreach_router,   tags=["outreach"])
app.include_router(watchlists_router, tags=["watchlists"])
app.include_router(alerts_router,     tags=["alerts"])
app.include_router(admin_router,      tags=["admin"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/live")
async def live():
    return {"status": "live"}


@app.get("/health/ready")
async def ready():
    return {"status": "ready"}
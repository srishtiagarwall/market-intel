import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine

logging.basicConfig(
    level=logging.INFO if settings.app_env == "production" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Market Intel API [{settings.app_env}]")

    from app.scheduler.job_runner import start_scheduler
    scheduler = start_scheduler()

    yield

    scheduler.shutdown(wait=False)
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Market Intel API",
    version="0.1.0",
    description="Personalised market signal engine for MF lump sum timing and stock signals.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routers import portfolio, signals_mf, signals_stock, watchlist

app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
app.include_router(signals_mf.router, prefix="/signals/mf", tags=["MF Signals"])
app.include_router(signals_stock.router, prefix="/signals/stocks", tags=["Stock Signals"])
app.include_router(watchlist.router, prefix="/watchlist", tags=["Watchlist"])


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "env": settings.app_env}

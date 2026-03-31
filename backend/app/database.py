from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ── SQLAlchemy ────────────────────────────────────────────────────────────────

# Neon (and any remote Postgres) requires SSL.
# asyncpg doesn't read ?sslmode= from the URL — pass ssl via connect_args instead.
_connect_args = {"ssl": "require"} if settings.database_url_requires_ssl else {}

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_pre_ping=True,
    pool_size=5,       # Neon serverless: keep pool small — connections are cheap to open
    max_overflow=10,
    connect_args=_connect_args,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session


# ── Redis ─────────────────────────────────────────────────────────────────────
# Redis is optional in development — used only for price caching.
# If unavailable, the app falls back to fetching live data on every request.

_redis_client: Redis | None = None


def get_redis() -> Redis | None:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not settings.redis_url:
        return None
    try:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        return _redis_client
    except Exception:
        return None

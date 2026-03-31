from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/market_intel"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/market_intel"

    @property
    def database_url_requires_ssl(self) -> bool:
        """True for Neon, Supabase, Railway, and any remote host. False for localhost."""
        return "localhost" not in self.database_url and "127.0.0.1" not in self.database_url

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # External APIs
    newsapi_key: str = ""
    screener_session_cookie: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Signal thresholds
    mf_signal_threshold: float = 60.0
    stock_signal_threshold: float = 70.0

    # MF scoring component max scores
    mf_drawdown_max: float = 40.0
    mf_valuation_max: float = 40.0
    mf_macro_max: float = 20.0

    # Stock scoring weights
    stock_fundamental_weight: float = 0.4
    stock_technical_weight: float = 0.4
    stock_event_weight: float = 0.2

    # Cache TTLs (seconds)
    price_cache_ttl: int = 300
    signal_cache_ttl: int = 3600


settings = Settings()

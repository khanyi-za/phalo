"""Environment configuration. Fail-fast at import time on missing values
(same philosophy as nuwa's PayfastConfig/ShipLogicConfig boot validation)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PHALO_", extra="ignore")

    # Shared Postgres (same instance as nuwa). Use the dedicated phalo role in
    # deployed environments — SELECT on public.*, ALL on schema phalo.
    database_url: str

    # Static shared secret for the internal API (nuwa → phalo, server-to-server).
    service_token: str

    environment: str = "development"

    @property
    def async_database_url(self) -> str:
        """Runtime engine URL (asyncpg driver)."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    @property
    def sync_database_url(self) -> str:
        """Alembic migration URL (psycopg driver)."""
        return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment

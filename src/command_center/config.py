from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MABDC Command Center"
    app_env: str = "local"
    app_base_url: str = "http://127.0.0.1:8088"
    private_access_note: str = "Use Tailscale or ZeroTier only"

    database_url: str
    telegram_bot_token: str | None = None
    telegram_approval_chat_id: str | None = None
    command_center_secret_dir: str = Field(default="/DATA/docker/command-center/secrets")

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_approval_chat_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()

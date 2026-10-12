from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DCMSIM_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/dcmsim.db"
    connect_timeout: float = 5
    association_timeout: float = 10
    dimse_timeout: float = 20
    max_upload_bytes: int = 50 * 1024 * 1024
    log_level: str = "INFO"
    proxy_auth_enabled: bool = False
    proxy_auth_required: bool = False
    proxy_user_header: str = "X-Forwarded-User"
    trusted_proxies: str = "127.0.0.1"
    static_path: str | None = None

    def ensure_data_directory(self) -> None:
        if self.database_url.startswith("sqlite:///"):
            path = self.database_url.removeprefix("sqlite:///")
            if path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()


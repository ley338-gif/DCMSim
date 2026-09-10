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

    def ensure_data_directory(self) -> None:
        if self.database_url.startswith("sqlite:///"):
            path = self.database_url.removeprefix("sqlite:///")
            if path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()


"""Environment configuration; no import-time I/O or global settings singleton."""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AMOS_", env_file=".env", extra="ignore", frozen=True
    )

    database_path: Path = Path("data/amos.sqlite3")
    provider: Literal["local"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    api_token: SecretStr | None = None

    @field_validator("api_token", mode="before")
    @classmethod
    def empty_token(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("api_token")
    @classmethod
    def valid_token(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            token = value.get_secret_value()
            if len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
                raise ValueError(
                    "API token must be at least 32 ASCII characters without whitespace"
                )
        return value

    @field_validator("database_path")
    @classmethod
    def file_database(cls, value: Path) -> Path:
        if str(value) == ":memory:":
            raise ValueError("Use a file-backed database for durable workflows")
        return value

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

import yaml


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-12-01-preview"


settings = Settings()

_config_cache: dict | None = None


def get_sommelier_config() -> dict:
    global _config_cache
    if _config_cache is None:
        config_path = Path(__file__).parent / "config" / "sommelier.yaml"
        with open(config_path) as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache

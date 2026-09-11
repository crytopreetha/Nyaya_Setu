from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://nyayasetu:nyayasetu_dev_password@db:5432/nyayasetu"

    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model_extraction: str = "gpt-4o-mini"
    openai_model_explanation: str = "gpt-4o-mini"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    whisper_model_size: str = "tiny"  # tiny | base | small — bigger = more accurate, slower

    storage_dir: str = "/app/storage_data"
    knowledge_base_dir: str = "/app/knowledge-base"

    max_upload_bytes: int = 25 * 1024 * 1024  # 25 MB

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

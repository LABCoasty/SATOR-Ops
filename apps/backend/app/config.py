from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "dev-secret-key-change-in-production"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sator"

    allowed_origins: List[str] = ["http://localhost:3000"]

    kairo_api_key: str = ""
    kairo_api_url: str = ""

    leanmcp_registry_url: str = ""

    arize_api_key: Optional[str] = None
    arize_space_key: Optional[str] = None

    browserbase_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

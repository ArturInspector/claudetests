from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Socratic API"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql+asyncpg://app:app@localhost:5432/socratic",
        description="Async SQLAlchemy database URL",
    )
    jwt_secret: str = Field(default="dev-secret", min_length=8)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    openrouter_api_key: str | None = None
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_fallback_model: str | None = "openai/gpt-4o-mini"
    openrouter_embedding_model: str = "openai/text-embedding-3-small"
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    chromadb_collection_prefix: str = "user"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "socratic_graph_2024"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_asyncpg(cls, value: str) -> str:
        """Allow postgres URLs without explicit async driver."""
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


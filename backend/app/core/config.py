from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    API_V1_STR: str

    # Security
    SECRET_KEY: str  # Should be changed in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    SECURE_COOKIES: bool = True

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json

            return json.loads(v)
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    DATABASE_URI: Union[str, None] = None

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str):
            return v

        values = info.data
        # Build Postgres DSN
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_SERVER"),
                port=values.get("POSTGRES_PORT"),
                path=f"{values.get('POSTGRES_DB') or ''}",
            )
        )

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_URL: Union[str, None] = None

    @field_validator("REDIS_URL", mode="before")
    def assemble_redis_url(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str):
            return v
        values = info.data
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/0"

    # Qdrant
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_URL: Union[str, None] = None
    QDRANT_API_KEY: Union[str, None] = None

    @field_validator("QDRANT_URL", mode="before")
    def assemble_qdrant_url(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str):
            return v
        values = info.data
        return f"http://{values.get('QDRANT_HOST')}:{values.get('QDRANT_PORT')}"

    # External APIs
    OPENAI_API_KEY: Union[str, None] = None
    ANTHROPIC_API_KEY: Union[str, None] = None

    # Phoenix
    PHOENIX_COLLECTOR_ENDPOINT: str

    # S3 / MinIO
    # S3 / MinIO
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str
    S3_REGION: str = "us-east-1"

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

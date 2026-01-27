from typing import List, Union, Optional
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

    @field_validator("SECRET_KEY")
    def check_secret_key(cls, v: str) -> str:
        if v == "changeme_production_key_here":
            import warnings

            warnings.warn(
                "SECRET_KEY is set to default value. Change this in production!",
                UserWarning,
            )
        return v

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

    @field_validator("DATABASE_URI", mode="after")
    def assemble_db_connection(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str):
            return v

        # Build Postgres DSN
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=info.data.get("POSTGRES_USER"),
                password=info.data.get("POSTGRES_PASSWORD"),
                host=info.data.get("POSTGRES_SERVER"),
                port=info.data.get("POSTGRES_PORT"),
                path=f"{info.data.get('POSTGRES_DB') or ''}",
            )
        )

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_URL: Union[str, None] = None

    @field_validator("REDIS_URL", mode="after")
    def assemble_redis_url(cls, v: Union[str, None], info) -> str:
        if isinstance(v, str):
            return v
        return f"redis://{info.data.get('REDIS_HOST')}:{info.data.get('REDIS_PORT')}/0"

    # External APIs
    OPENAI_API_KEY: Union[str, None] = None
    GOOGLE_API_KEY: Union[str, None] = None
    COHERE_API_KEY: Union[str, None] = None

    # Email
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    @property
    def EMAILS_ENABLED(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # Phoenix
    PHOENIX_COLLECTOR_ENDPOINT: str

    # S3 / MinIO
    # S3 / MinIO
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str
    S3_REGION: str = "us-east-1"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB default
    ALLOWED_UPLOAD_CONTENT_TYPES: List[str] = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "text/csv",
    ]

    @field_validator("ALLOWED_UPLOAD_CONTENT_TYPES", mode="before")
    def assemble_allowed_content_types(
        cls, v: Union[str, List[str]]
    ) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json

            return json.loads(v)
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # Vector Database (pgvector) Configuration
    # Index type: "hnsw" (default, better query performance) or "ivfflat" (faster build)
    VECTOR_INDEX_TYPE: str = "hnsw"
    # Distance metric: "cosine" (default), "l2", or "inner_product"
    VECTOR_DISTANCE_METRIC: str = "cosine"
    # Embedding dimensions (should match your embedding model output)
    VECTOR_EMBEDDING_DIMENSIONS: int = 1536

    # HNSW index parameters
    VECTOR_HNSW_M: int = 16  # Max connections per node (2-100)
    VECTOR_HNSW_EF_CONSTRUCTION: int = 64  # Dynamic candidate list size (4-1000)

    # IVFFlat index parameters
    VECTOR_IVFFLAT_LISTS: int = 100  # Number of inverted lists (1-10000)

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        case_sensitive=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def get_vector_config():
    """
    Get VectorConfig instance from current settings.

    Returns a configured VectorConfig object based on environment variables.
    """
    from app.core.vector_config import (
        VectorConfig,
        VectorIndexType,
        DistanceMetric,
        HNSWConfig,
        IVFFlatConfig,
    )

    return VectorConfig(
        index_type=VectorIndexType(settings.VECTOR_INDEX_TYPE),
        distance_metric=DistanceMetric(settings.VECTOR_DISTANCE_METRIC),
        embedding_dimensions=settings.VECTOR_EMBEDDING_DIMENSIONS,
        hnsw=HNSWConfig(
            m=settings.VECTOR_HNSW_M,
            ef_construction=settings.VECTOR_HNSW_EF_CONSTRUCTION,
        ),
        ivfflat=IVFFlatConfig(
            lists=settings.VECTOR_IVFFLAT_LISTS,
        ),
    )

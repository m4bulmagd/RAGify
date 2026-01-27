from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.main import api_router
from contextlib import asynccontextmanager
from app.core.db import init_db
import app.core.celery_app  # Ensure Celery app is loaded


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.core.notifications import manager
    await manager.start_redis_listener()
    yield
    # Shutdown
    await manager.stop_redis_listener()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "Welcome to RAGify API"}

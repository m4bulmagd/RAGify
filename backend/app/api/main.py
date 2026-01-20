from fastapi import APIRouter
from app.api.routes import health, login, users, projects, agents, chats, documents

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

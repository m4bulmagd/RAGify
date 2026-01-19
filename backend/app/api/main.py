from fastapi import APIRouter
from app.api.routes import health, login, users, projects

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
# Will include other routers like users, login, etc. here later

from fastapi import APIRouter

from app.api.routes.agent_tools import router as agent_tools_router
from app.api.routes.health import router as health_router
from app.api.routes.products import router as products_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(agent_tools_router)
api_router.include_router(products_router)

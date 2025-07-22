from fastapi import APIRouter
from .tracks import router as tracks_router
from .chat import router as chat_router
from .tasks import router as tasks_router

api_router = APIRouter(prefix="/api")

api_router.include_router(tracks_router)
api_router.include_router(chat_router)
api_router.include_router(tasks_router)

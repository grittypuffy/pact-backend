from fastapi import APIRouter

from ..auth import router as auth_router
from ..chat import router as chat_router
from ..llm import router as llm_router
from ..history import router as history_router
from ..statistics import router as statistics_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth")
router.include_router(chat_router, prefix="/chat")
router.include_router(llm_router, prefix="/llm")
router.include_router(history_router, prefix="/history")
router.include_router(statistics_router, prefix="/statistics")
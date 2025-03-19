from fastapi import APIRouter

from ..auth import router as auth_router
from ..chat import router as chat_router
from ..history import router as history_router
from ...helpers.auth import decode_jwt

router = APIRouter()

router.include_router(auth_router, prefix="/auth")
router.include_router(chat_router, prefix="/chat")
router.include_router(history_router, prefix="/history")
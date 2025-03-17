from fastapi import APIRouter

from ..auth import router as auth_router
# from ..chat import router as chat_router
from pact_backend.helpers.auth import decode_jwt

router = APIRouter()

router.include_router(auth_router, prefix="/auth")
# router.include_router(chat_router, prefix="/chat")

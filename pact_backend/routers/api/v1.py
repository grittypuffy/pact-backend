from fastapi import APIRouter

from revil_backend.routers.auth import router as auth_router
from revil_backend.helpers.auth import decode_jwt

router = APIRouter()

router.include_router(auth_router, prefix="/auth")

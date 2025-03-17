from fastapi import APIRouter

from pact_backend.routers.auth import router as auth_router
from pact_backend.helpers.auth import decode_jwt

router = APIRouter()

router.include_router(auth_router, prefix="/auth")

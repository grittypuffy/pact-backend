import asyncio
import os
import re
import time
import datetime
from typing import List, Annotated

from fastapi import APIRouter, Response, Request, Cookie
from fastapi.responses import JSONResponse

from ..config import AppConfig, get_config
from ..models.auth import SignInRequest, SignUpRequest, Token
from ..helpers.auth import get_hashed_password, verify_password, sign_jwt, decode_jwt
from ..services.response_generator import BotHandler

router = APIRouter()

config: AppConfig = get_config()


@router.get("/{user_prompt}")
async def get_bot_response(user_prompt: str):
    try:
        bot_handler = BotHandler()
        bot_response = bot_handler.get_response(user_prompt)
        opt_prompt = bot_handler.get_response(
            f'Please analyze the given prompt and optimize it by removing any grammatical errors, spelling mistakes, biases (such as gender, racial, or cultural biases), sensitive or personal information, inappropriate content (such as self-harm, violence, or explicit material), and any unclear or incomplete phrasing. Ensure the optimized prompt is structured for clarity, neutrality, and inclusivity, making it more effective in generating meaningful and constructive responses only prompt no explanation."{user_prompt}"'
        )
        opt_bot_response = bot_handler.get_response(opt_prompt["response"])
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": {
                    "bot_response": bot_response,
                    "opt_bot_response": opt_bot_response,
                    "opt_prompt": opt_prompt,
                },
            },
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "message": "An internal error occured"},
        )

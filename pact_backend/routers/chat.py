import asyncio
import os
import re
import time
import datetime
from typing import List, Annotated

from fastapi import APIRouter, Response, Request, Cookie
from fastapi.responses import JSONResponse

from ..services.metrics import Metrics
from ..config import AppConfig, get_config
from ..models.auth import SignInRequest, SignUpRequest, Token
from ..helpers.auth import get_hashed_password, verify_password, sign_jwt, decode_jwt
from ..services.response import BotHandler

router = APIRouter()

config: AppConfig = get_config()


@router.get("/{prompt}")
async def generate_response(prompt: str):
    try:
        bot_handler = BotHandler()
        bot_response = bot_handler.get_response(prompt)
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

@router.post("/metrics")
async def get_metrics(query:str, answer: str ):
    try:
        metrics = Metrics()
        response = metrics.evaluate_all(query, answer)
        evaluation = {}
        evaluation["grammar"] = response['grammar']
        evaluation["spell_check"] = response['spell_check']
        maxi = -1
        if "sensitive_info" in response and isinstance(response["sensitive_info"], list) and response["sensitive_info"]:
            entities = response["sensitive_info"][0].entities
            for ele in entities:
                maxi = max(maxi, ele.get('confidence_score', -1))

            maxi = int((maxi * 10) // 2)
        else:
            maxi = -1

        evaluation["sensitive_info"] = maxi
        evaluation["violence"] = response["violence"]["violence_score"]
        evaluation["bias_gender"] = response["bias_gender"]["sexual_score"]
        evaluation["self_harm"] = response["bias_self_harm"]["self_harm_score"]
        evaluation["hate_unfairness"] = response["hate_unfairness"]["hate_unfairness_score"]
        flag = "not computed"
        for key in response["jailbreak"]:
            if response["jailbreak"][key] == True:
                flag = True
                break
            else : flag = False
        evaluation["jailbreak"] = flag
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": {
                    "metrics": evaluation
                },
            },
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "message": "An internal error occured"},
        )
    
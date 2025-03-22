import asyncio
import os
import math
from pydantic import BaseModel
import logging
from typing import List, Annotated, Optional

import azure.cognitiveservices.speech as speechsdk
from fastapi import APIRouter, Response, Request, Cookie, File, Form, UploadFile
from fastapi.responses import JSONResponse

from ..config import AppConfig, get_config
from ..helpers.auth import (
    get_hashed_password,
    verify_password,
    sign_jwt,
    decode_jwt,
    verify_jwt,
)
from ..models.auth import SignInRequest, SignUpRequest, Token
from ..services.metrics import Metrics
from ..services.response import BotHandler
from ..services.upload import FileUpload

router = APIRouter()

config: AppConfig = get_config()

upload_client: FileUpload = FileUpload()

bot_handler = BotHandler()


class Metric_Request(BaseModel):
    query: str
    answer: str
    opt_query: str
    opt_answer: str
    flagged: bool
    metrics: dict | None


class BotRequest(BaseModel):
    prompt: str


@router.post("/prompt")
async def get_bot_response(prompt: BotRequest):
    try:
        prompt = prompt.prompt
        metrics = Metrics()
        bot_response = bot_handler.get_response(prompt)
        opt_prompt = bot_handler.get_response(
            f'Please analyze the given prompt and optimize it by removing any grammatical errors, spelling mistakes, biases (such as gender, racial, or cultural biases), sensitive or personal information, inappropriate content (such as self-harm, violence, or explicit material), and any unclear or incomplete phrasing. Ensure the optimized prompt is structured for clarity, neutrality, and inclusivity, making it more effective in generating meaningful and constructive responses only prompt no explanation."{prompt}"'
        )
        opt_bot_response = bot_handler.get_response(opt_prompt["response"])
        if bot_response.get("content_filter"):
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "data": {
                        "flagged": True,
                        "bot_response": {
                            "response": "The provided prompt was filtered due to the prompt triggering the content management policy. Please modify your prompts"
                        },
                        "opt_bot_response": opt_bot_response,
                        "opt_prompt": opt_prompt,
                        "metrics": metrics.get_openai_metrics(bot_response, prompt),
                    },
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "bot_response": bot_response,
                    "opt_bot_response": opt_bot_response,
                    "opt_prompt": opt_prompt,
                    "flagged": False,
                    "metrics": None,
                },
            },
        )

    except Exception as e:
        logging.error(e)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "message": "An internal error occured"},
        )


@router.post("/metrics")
async def get_metrics(payload: Metric_Request):
    try:
        metrics = Metrics()
        response = None
        opt_response = None

        if payload.flagged:
            response = metrics.get_openai_metrics(payload.metrics, payload.query)
            opt_response = metrics.evaluate_all(payload.opt_query, payload.opt_answer)
            opt_evaluation = {}
            opt_evaluation["grammar"] = int(opt_response["grammar"])
            opt_evaluation["spell_check"] = int(opt_response["spell_check"])
            maxi = 0
            if (
                "sensitive_info" in opt_response
                and isinstance(opt_response["sensitive_info"], list)
                and opt_response["sensitive_info"]
            ):
                entities = opt_response["sensitive_info"][0].entities
                for ele in entities:
                    maxi = max(maxi, ele.get("confidence_score", 0))

                maxi = int(math.floor(maxi * 5))
            else:
                maxi = 0
            opt_evaluation["sensitive_info"] = maxi
            opt_evaluation["violence"] = int(
                opt_response["violence"]["violence_score"] * 5 / 7
            )
            opt_evaluation["bias_gender"] = int(
                opt_response["bias_gender"]["sexual_score"] * 5 / 7
            )
            opt_evaluation["self_harm"] = int(
                opt_response["bias_self_harm"]["self_harm_score"] * 5 / 7
            )
            opt_evaluation["hate_unfairness"] = int(
                opt_response["hate_unfairness"]["hate_unfairness_score"] * 5 / 7
            )
            flag = "not computed"
            for key in opt_response["jailbreak"]:
                if opt_response["jailbreak"][key] == True:
                    flag = True
                    break
                else:
                    flag = False
            opt_evaluation["jailbreak"] = flag

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "data": {"metrics": response, "opt_metrics": opt_evaluation},
                },
            )

        else:
            response = metrics.evaluate_all(payload.query, payload.answer)
            opt_response = metrics.evaluate_all(payload.opt_query, payload.opt_answer)

        evaluation = {}
        opt_evaluation = {}

        evaluation["grammar"] = int(response["grammar"])
        opt_evaluation["grammar"] = int(opt_response["grammar"])

        evaluation["spell_check"] = int(response["spell_check"])
        opt_evaluation["spell_check"] = int(opt_response["spell_check"])

        maxi = 0
        if (
            "sensitive_info" in response
            and isinstance(response["sensitive_info"], list)
            and response["sensitive_info"]
        ):
            entities = response["sensitive_info"][0].entities
            for ele in entities:
                maxi = max(maxi, ele.get("confidence_score", 0))
            maxi = int(math.ceil((maxi * 5)))
        else:
            maxi = 0
        evaluation["sensitive_info"] = maxi

        maxi = 0
        if (
            "sensitive_info" in opt_response
            and isinstance(opt_response["sensitive_info"], list)
            and opt_response["sensitive_info"]
        ):
            entities = opt_response["sensitive_info"][0].entities
            for ele in entities:
                maxi = max(maxi, ele.get("confidence_score", 0))

            maxi = int(math.floor(maxi * 5))
        else:
            maxi = 0
        opt_evaluation["sensitive_info"] = maxi

        evaluation["violence"] = int(response["violence"]["violence_score"] * 5 / 7)
        opt_evaluation["violence"] = int(
            opt_response["violence"]["violence_score"] * 5 / 7
        )

        evaluation["bias_gender"] = int(response["bias_gender"]["sexual_score"] * 5 / 7)
        opt_evaluation["bias_gender"] = int(
            opt_response["bias_gender"]["sexual_score"] * 5 / 7
        )

        evaluation["self_harm"] = int(
            response["bias_self_harm"]["self_harm_score"] * 5 / 7
        )
        opt_evaluation["self_harm"] = int(
            opt_response["bias_self_harm"]["self_harm_score"] * 5 / 7
        )

        evaluation["hate_unfairness"] = int(
            response["hate_unfairness"]["hate_unfairness_score"] * 5 / 7
        )
        opt_evaluation["hate_unfairness"] = int(
            opt_response["hate_unfairness"]["hate_unfairness_score"] * 5 / 7
        )

        flag = "not computed"
        for key in response["jailbreak"]:
            if response["jailbreak"][key] == True:
                flag = True
                break
            else:
                flag = False
        evaluation["jailbreak"] = flag

        flag = "not computed"
        for key in opt_response["jailbreak"]:
            if opt_response["jailbreak"][key] == True:
                flag = True
                break
            else:
                flag = False
        opt_evaluation["jailbreak"] = flag

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {"metrics": evaluation, "opt_metrics": opt_evaluation},
            },
        )
    except Exception as e:
        logging.error(e)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "message": "An internal error occured"},
        )


@router.post("/voice")
async def get_voice_response(
    audio: Annotated[UploadFile, File()],
    language_code: str = Form("en-US"),
    token: str = Cookie(None),
):
    if token and not verify_jwt(token):
        return JSONResponse(
            status_code=409,
            content={"status": "failed", "message": "Invalid credentials"},
        )
    token = None
    username = None
    user_id = None
    if token:
        token = decode_jwt(token)
        user_id = token.get("user_id")
        username = token.get("username")
    content_type = audio.content_type
    print(content_type)
    file_path, url = await upload_client.upload_file(user_id, username, audio)

    if not url:
        return JSONResponse(
            status_code=422,
            content={
                "status": "failed",
                "data": None,
                "message": "Failed to process voice content",
            },
        )
    prompt = None
    match content_type:
        case "audio/wav" | "video/webm":
            transcription = await upload_client.get_audio_transcription(
                file_path, language_code
            )
            if (
                transcripted_text := transcription.get("data")
            ) and not transcription.get("error"):
                prompt = transcripted_text

        case _:
            return JSONResponse(
                status_code=406,
                content={
                    "status": "failed",
                    "data": None,
                    "message": "Unsupported format",
                },
            )
    try:
        if not prompt:
            return JSONResponse(
                status_code=406,
                content={
                    "status": "failed",
                    "data": None,
                    "message": "There was an error while processing the prompt",
                },
            )
        bot_response = bot_handler.get_response(prompt)

        opt_prompt = bot_handler.get_response(
            f'Please analyze the given prompt and optimize it by removing any grammatical errors, spelling mistakes, biases (such as gender, racial, or cultural biases), sensitive or personal information, inappropriate content (such as self-harm, violence, or explicit material), and any unclear or incomplete phrasing. Ensure the optimized prompt is structured for clarity, neutrality, and inclusivity, incorporating responsible AI principles making it more effective in generating meaningful and constructive responses only prompt no explanation.\n"{prompt}"'
        )

        opt_bot_response = bot_handler.get_response(opt_prompt["response"])

        if bot_response.get("content_filter"):
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "data": {
                        "flagged": True,
                        "prompt": transcripted_text,
                        "bot_response": {
                            "response": "The provided prompt was filtered due to the prompt triggering the content management policy. Please modify your prompts"
                        },
                        "opt_bot_response": opt_bot_response,
                        "opt_prompt": opt_prompt,
                    },
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "flagged": False,
                    "prompt": transcripted_text,
                    "bot_response": {"response": bot_response.get("response")},
                    "opt_bot_response": opt_bot_response,
                    "opt_prompt": opt_prompt,
                },
            },
        )

    except Exception as e:
        logging.error(e)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "message": "An internal error occured"},
        )

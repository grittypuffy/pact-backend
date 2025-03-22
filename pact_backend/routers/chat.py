import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from bson import ObjectId

from ..config import AppConfig, get_config
from ..models.chat import ChatModel, RequestModel
from ..helpers.serializer import serializer

router = APIRouter()
config: AppConfig = get_config()
db = config.db


@router.get("/get")
async def get_chat(req: Request):
    try:
        user_id = req.state.user.get("user_id")
        HistoryCollection = db['history']
        history_cursor = HistoryCollection.find({"user_id":user_id},{"created_at": 0})
        history = await history_cursor.to_list()
        history = list(reversed(history))
        chats = []

        if history:
            ChatCollection = db['chat']
            for h in history:
                chat_cursor = ChatCollection.find({"history_id":str(h["_id"])},{"created_at": 0})
                chat = await chat_cursor.to_list()
                chat = [serializer(c) for c in chat]
                chats.append({"history":serializer(h),"chats":chat})
        return JSONResponse(status_code=200,content={"status": "success","data": chats})
    except Exception as err:
        logging.error(err)
        return JSONResponse(status_code=500,content={"status": "failed","message": "Internal server error"})


@router.post("/add")
async def add_chat(body: RequestModel):
    try:
        HistoryCollection = db['history']
        history = await HistoryCollection.find_one({"_id": ObjectId(body.history_id)})

        if not history:
            return JSONResponse(status_code=404,content={"status": "failed","message": "Conversation not found"})

        data = ChatModel(**body.dict())
        ChatCollection = db['chat']
        await ChatCollection.insert_one(data.dict())

        return JSONResponse(status_code=200,content={"status": "success","message": "Chat added successfully"})

    except Exception as err:
        logging.error(err)
        return JSONResponse(status_code=500,content={"status": "failed","message": "Internal server error"})

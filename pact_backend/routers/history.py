import logging
from ..config import AppConfig, get_config
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ..models.history import HistoryModel
from bson import ObjectId
from ..services.response import BotHandler
from ..helpers.serializer import serializer

router = APIRouter()
config: AppConfig = get_config()
db = config.db

@router.post("/add")
async def add_history(user_msg: str,req: Request):
    try:
        user_id = req.state.user.get("user_id")
        prompt = f"For the following message '{user_msg}' give me a proper title for the chat. The length of the title should not be more than 3 words"
        bot = BotHandler()
        title = bot.get_response(prompt).get("response").replace("\n","").replace("\"","")
        data = HistoryModel(title=title, user_id=user_id)
        collection = db['history']
        data = await collection.insert_one(data.dict())
        id = str(data.inserted_id)
        return JSONResponse(status_code=200,content={"status": "success","message": "History added successfully", "data": id, "title": title})
    except Exception as err:
        logging.error(err)
        return JSONResponse(status_code=500,content={"status": "failed","message": "Internal server error"})

@router.get("/get")
async def get_history(req:Request):
    try:
        user_id = req.state.user.get("user_id")
        collection = db['history']
        history_cursor = collection.find({"user_id":user_id},{"created_at":0}).sort("created_at",1)
        history = await history_cursor.to_list()
        history = [serializer(hist) for hist in history]
        return JSONResponse(status_code=200,content={"status": "success","data": history})
    except Exception as err:
        logging.error(err)
        return JSONResponse(status_code=500,content={"status": "failed","message": "Internal server error"})
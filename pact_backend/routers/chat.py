from bson import ObjectId
from ..models.chat import ChatModel, RequestModel
from ..config import AppConfig, get_config
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ..helpers.serializer import serializer

router = APIRouter()
config: AppConfig = get_config()
db = config.db

@router.post("/add")
async def addChat(body:RequestModel, req: Request):
    try:
        body_data = {}
        body = body.dict()
        for key in body:
            if key=="prompt_metrics":
                for mkey in body[key]:
                    body_data[mkey] = body[key][mkey]
            elif key=="opt_prompt_metrics":
                for mkey in body[key]:
                    body_data["opt_"+mkey] = body[key][mkey]
            else:
                body_data[key] = body[key]
        HistoryCollection = db['history']
        history = await HistoryCollection.find_one({"_id":ObjectId(body_data.get("history_id"))})
        if not history:
            return JSONResponse(status_code=404,content={"status": "failed","message": "Conversation not found"})
        ChatCollection = db['chat']
        chat_id = body_data.get("chat_id")
        del body_data["chat_id"]
        if not chat_id:
            data = ChatModel(**body_data)
            insert_data = await ChatCollection.insert_one(data.dict())
            chat_id = str(insert_data.inserted_id)
            return JSONResponse(status_code=200,content={"status": "success","message": "Chat added successfully"})
        chat_id = ObjectId(chat_id)
        prevChat = await ChatCollection.find_one({"_id":chat_id})
        if not prevChat:
            return JSONResponse(status_code=404,content={"status": "failed","message": "Chat not found"})
        created_at = prevChat.get("created_at")
        data = ChatModel(**{k:v for k,v in body_data.items() if k != "chat_id"}, created_at=created_at)
        await ChatCollection.update_one({"_id":chat_id}, {"$set": data.dict()})
        return JSONResponse(status_code=200,content={"status": "success","message": "Chat updated successfully"})
    except Exception as err:
        print(err)
        return JSONResponse(status_code=500,content={"status": "failed","message": f"Internal server error{err}"})

# @router.put("/update")
# async def updateChat(body:UpdateRequest):
#     try:
#         collection = db['chat']
#         chat_id = ObjectId(body.chat_id)
#         prevChat = await collection.find_one({"_id":chat_id})
#         if not prevChat:
#             return JSONResponse(status_code=404,content={"status": "failed","message": "Chat not found"})
#         history_id = prevChat.get("history_id")
#         data = ChatModel(**{k:v for k,v in body.dict().items() if k != "chat_id"}, history_id=history_id)
#         await collection.update_one({"_id":chat_id}, {"$set": data.dict()})
#         return JSONResponse(status_code=200,content={"status": "success","message": "Chat updated successfully"})
#     except Exception as err:
#         print(err)
#         return JSONResponse(status_code=500,content={"status": "failed","message": "Internal server error"})

# @router.get("/get")
# async def getChat(history_id:str):
#     try:
#         collection = db['chat']
#         chats_cursor = collection.find({"history_id":history_id},{"created_at": 0}).sort("created_at",1)
#         chats = await chats_cursor.to_list()
#         chats = [serializer(chat) for chat in chats]
#         if not chats:
#             return JSONResponse(status_code=404,content={"status": "failed","message": "Chat not found"})
#         return JSONResponse(status_code=200,content={"status": "success","data": chats})
#     except Exception as err:
#         print(err)
#         return JSONResponse(status_code=500,content={"status": "failed","message": "Internal server error"})

@router.get("/get")
async def getChat(req:Request):
    try:
        user_id = req.state.user.get("user_id")
        HistoryCollection = db['history']
        history_cursor = HistoryCollection.find({"user_id":user_id},{"created_at": 0}).sort("created_at",1)
        history = await history_cursor.to_list()
        chats = []
        if history:
            ChatCollection = db['chat']
            for h in history:
                chat_cursor = ChatCollection.find({"history_id":str(h["_id"])},{"created_at": 0}).sort("created_at",1)
                chat = await chat_cursor.to_list()
                chat = [serializer(c) for c in chat]
                chats.append({"history":serializer(h),"chats":chat})
        return JSONResponse(status_code=200,content={"status": "success","data": chats})
    except Exception as err:
        print(err)
        return JSONResponse(status_code=500,content={"status": "failed","message": "Internal server error"})
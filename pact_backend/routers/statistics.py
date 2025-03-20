import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..config import AppConfig, get_config

from ..models.statistics import StatisticsModel, RequestModel

router = APIRouter()
config: AppConfig = get_config()
db = config.db

@router.post("/add")
async def update_statistics(body: RequestModel):
    try:
        collection = db["statistics"]
        prompt_metrics = await collection.find_one({"metrics_type":"prompt_metrics"})
        opt_prompt_metrics = await collection.find_one({"metrics_type":"opt_prompt_metrics"})
        if prompt_metrics is None:
            prompt_metrics = StatisticsModel(metrics_type="prompt_metrics")
            prompt_metrics = prompt_metrics.dict()
        else:
            del prompt_metrics["_id"]
        if opt_prompt_metrics is None:
            opt_prompt_metrics = StatisticsModel(metrics_type="opt_prompt_metrics")
            opt_prompt_metrics = opt_prompt_metrics.dict()
        else:
            del opt_prompt_metrics["_id"]
        prompt_metrics["count"] += 1
        opt_prompt_metrics["count"] += 1
        for key in body.metrics.dict().keys():
            prompt_metrics[key][str(body.metrics.dict()[key])] += 1
            opt_prompt_metrics[key][str(body.opt_metrics.dict()[key])] += 1
        await collection.replace_one({"metrics_type":"prompt_metrics"},prompt_metrics,upsert=True)
        await collection.replace_one({"metrics_type":"opt_prompt_metrics"},opt_prompt_metrics,upsert=True)
        return JSONResponse(status_code=200,content={"status": "success","message": "Statistics updated successfully"})
    except Exception as err:
        logging.error(err)
        return JSONResponse(status_code=500,content={"status": "failed","message": "Internal server error"})

@router.get("/get")
async def get_statistics():
    try:
        collection = db["statistics"]
        prompt_metrics = await collection.find_one({"metrics_type":"prompt_metrics"})
        opt_prompt_metrics = await collection.find_one({"metrics_type":"opt_prompt_metrics"})
        if prompt_metrics is None:
            prompt_metrics = StatisticsModel(metrics_type="prompt_metrics")
            prompt_metrics = prompt_metrics.dict()
        else:
            del prompt_metrics["_id"]
        if opt_prompt_metrics is None:
            opt_prompt_metrics = StatisticsModel(metrics_type="opt_prompt_metrics")
            opt_prompt_metrics = opt_prompt_metrics.dict()
        else:
            del opt_prompt_metrics["_id"]
        return JSONResponse(status_code=200,content={"status": "success","data":{"prompt_metrics": prompt_metrics,"opt_prompt_metrics": opt_prompt_metrics}})
    except Exception as err:
        logging.error(err)
        return JSONResponse(status_code=500,content={"status": "failed","message": "Internal server error"})
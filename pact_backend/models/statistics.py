from pydantic import BaseModel, Field
from typing import Dict

from .chat import MetricsModel

def default_metrics():
    return {
        '0':0,
        '1':0,
        '2':0,
        '3':0,
        '4':0,
        '5':0
    }

class StatisticsModel(BaseModel):
    metrics_type: str
    count: int = Field(default=0)
    grammar: Dict[str,int] = Field(default_factory=default_metrics)
    spell_check: Dict[str,int] = Field(default_factory=default_metrics)
    sensitive_info: Dict[str,int] = Field(default_factory=default_metrics)
    violence: Dict[str,int] = Field(default_factory=default_metrics)
    bias_gender: Dict[str,int] = Field(default_factory=default_metrics)
    self_harm: Dict[str,int] = Field(default_factory=default_metrics)
    hate_unfairness: Dict[str,int] = Field(default_factory=default_metrics)
    jailbreak: Dict[str,int] = Field(default_factory=lambda: {'True':0,'False':0})

class RequestModel(BaseModel):
    metrics: MetricsModel
    opt_metrics: MetricsModel
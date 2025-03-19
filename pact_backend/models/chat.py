from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ChatModel(BaseModel):
    history_id: str
    prompt: str
    opt_prompt: str
    response: str
    opt_response: str
    grammar: int 
    spell_check: int 
    sensitive_info: int 
    violence: int 
    bias_gender: int 
    self_harm: int 
    hate_unfairness: int 
    jailbreak: bool 
    opt_grammar: int 
    opt_spell_check: int 
    opt_sensitive_info: int 
    opt_violence: int 
    opt_bias_gender: int 
    opt_self_harm: int 
    opt_hate_unfairness: int 
    opt_jailbreak: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MetricsModel(BaseModel):
    grammar: int 
    spell_check: int 
    sensitive_info: int 
    violence: int 
    bias_gender: int 
    self_harm: int 
    hate_unfairness: int 
    jailbreak: bool

class RequestModel(BaseModel):
    history_id: str
    chat_id: Optional[str] = None
    prompt: str
    opt_prompt: str
    response: str
    opt_response: str
    prompt_metrics: MetricsModel
    opt_prompt_metrics: MetricsModel

# class RequestModel(BaseModel):
#     history_id: str
#     chat_id: Optional[str] = None
#     prompt: str
#     opt_propmt: str
#     response: str
#     opt_response: str
#     grammar: int 
#     spell_check: int 
#     sensitive_info: int 
#     violence: int 
#     bias_gender: int 
#     self_harm: int 
#     hate_unfairness: int 
#     jailbreak: bool 
#     opt_grammar: int 
#     opt_spell_check: int 
#     opt_sensitive_info: int 
#     opt_violence: int 
#     opt_bias_gender: int 
#     opt_self_harm: int 
#     opt_hate_unfairness: int 
#     opt_jailbreak: bool

# class AddRequest(BaseModel):
#     history_id: str
#     prompt: str
#     opt_propmt: str
#     response: str
#     opt_response: str

# class UpdateRequest(BaseModel):
#     chat_id: str
#     prompt: str
#     opt_propmt: str
#     response: str
#     opt_response: str
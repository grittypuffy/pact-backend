from pydantic import BaseModel, Field
from datetime import datetime

class HistoryModel(BaseModel):
    user_id: str
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
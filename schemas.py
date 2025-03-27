from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any
from datetime import datetime

class JobDataCreate(BaseModel):
    job_id: UUID
    monai_history_days: Optional[int] = None  # Adicionado como campo separado
    attributes: Optional[Dict[str, Any]]

class JobDataResponse(JobDataCreate):
    id: UUID
    received_at: datetime
    weekday: str
    is_holiday: bool

    class Config:
        orm_mode = True
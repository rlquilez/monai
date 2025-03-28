from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # Roles: admin, operator, viewer

class UserResponse(BaseModel):
    id: UUID
    username: str
    role: str
    created_at: datetime

    class Config:
        orm_mode = True

class JobDataCreate(BaseModel):
    job_id: UUID
    name: str
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None

class JobDataResponse(JobDataCreate):
    id: UUID
    received_at: datetime
    weekday: str
    is_holiday: bool

    class Config:
        orm_mode = True

class RuleCreate(BaseModel):
    job_id: UUID
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class RuleResponse(RuleCreate):
    id: UUID

    class Config:
        orm_mode = True

class QueryLogResponse(BaseModel):
    id: UUID
    job_id: UUID
    received_at: datetime
    ip_address: str
    payload: Dict[str, Any]

    class Config:
        orm_mode = True
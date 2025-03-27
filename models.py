from sqlalchemy import Column, String, JSON, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class JobData(Base):
    __tablename__ = "job_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    attributes = Column(JSON, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    weekday = Column(String, nullable=False)
    is_holiday = Column(Boolean, nullable=False)

class QueryLog(Base):
    __tablename__ = "query_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
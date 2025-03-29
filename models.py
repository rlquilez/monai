import os
from sqlalchemy import Column, String, JSON, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
from pytz import timezone

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
    attributes = Column(JSON, nullable=True)
    result = Column(String, nullable=False)  # Armazena o resultado ("true" ou "false")
    explanation = Column(Text, nullable=False)  # Armazena a explicação
    referer = Column(String, nullable=True)  # Armazena o referer do cabeçalho
    fingerprint = Column(String, nullable=False)  # Armazena o fingerprint
    received_at = Column(DateTime, default=lambda: datetime.now(timezone(os.getenv("TZ", "UTC"))), nullable=False)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)  # Nova coluna para armazenar o User-Agent
    monai_history_executions = Column(Integer, nullable=False)  # Número de execuções históricas consideradas
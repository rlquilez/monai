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
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone(os.getenv("TZ", "UTC"))), nullable=False)   # Adicionado timezone=True
    weekday = Column(String, nullable=False)  # Dia da semana
    month = Column(String, nullable=False)  # Novo campo para o mês
    is_holiday = Column(Boolean, default=False, nullable=False)

class QueryLog(Base):
    __tablename__ = "query_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    attributes = Column(JSON, nullable=True)
    result = Column(String, nullable=False)  # Armazena o resultado ("true" ou "false")
    explanation = Column(Text, nullable=False)  # Armazena a explicação
    referer = Column(String, nullable=True)  # Armazena o referer do cabeçalho
    fingerprint = Column(String, nullable=False)  # Armazena o fingerprint
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone(os.getenv("TZ", "UTC"))), nullable=False)  # Adicionado timezone=True
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)  # Nova coluna para armazenar o User-Agent
    monai_history_executions = Column(Integer, nullable=False)  # Número de execuções históricas consideradas
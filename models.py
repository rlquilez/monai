from sqlalchemy import Column, String, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Roles: admin, operator, viewer
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class JobData(Base):
    __tablename__ = "job_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)  # Friendly name for the job
    tags = Column(JSON, nullable=True)  # Tags for filtering
    attributes = Column(JSON, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    weekday = Column(String, nullable=False)
    is_holiday = Column(Boolean, nullable=False)

class Rule(Base):
    __tablename__ = "rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_data.job_id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)  # Tags for filtering

class QueryLog(Base):
    __tablename__ = "query_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
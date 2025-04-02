import os
from sqlalchemy import Column, String, JSON, DateTime, Boolean, Text, Integer, ForeignKey, Table, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from pytz import timezone

Base = declarative_base()

# Tabela de associação entre jobs e grupos de regras
job_rule_groups = Table(
    'job_rule_groups',
    Base.metadata,
    Column('job_id', String, ForeignKey('jobs.id', ondelete='CASCADE')),
    Column('rule_group_id', UUID, ForeignKey('rule_groups.id', ondelete='CASCADE'))
)

# Tabela de associação entre grupos de regras e regras
rule_group_rules = Table(
    'rule_group_rules',
    Base.metadata,
    Column('rule_group_id', UUID, ForeignKey('rule_groups.id', ondelete='CASCADE')),
    Column('rule_id', UUID, ForeignKey('rules.id', ondelete='CASCADE'))
)

class Rule(Base):
    __tablename__ = "rules"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    rule_text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relacionamentos
    rule_groups = relationship("RuleGroup", secondary=rule_group_rules, back_populates="rules")

class RuleGroup(Base):
    __tablename__ = "rule_groups"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relacionamentos
    rules = relationship("Rule", secondary=rule_group_rules, back_populates="rule_groups")
    jobs = relationship("Job", secondary=job_rule_groups, back_populates="rule_groups")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)  # SHA-256 do job_name + job_filename
    job_name = Column(String, nullable=False)
    job_filename = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relacionamentos
    job_data = relationship("JobData", back_populates="job", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="job", cascade="all, delete-orphan")
    rule_groups = relationship("RuleGroup", secondary=job_rule_groups, back_populates="jobs")

class JobData(Base):
    __tablename__ = "job_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    job_name = Column(String, nullable=False)
    job_filename = Column(String, nullable=False)
    attributes = Column(JSON, nullable=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone(os.getenv("TZ", "America/Sao_Paulo"))), nullable=False)
    weekday = Column(String, nullable=False)
    month = Column(String, nullable=False)
    is_holiday = Column(Boolean, default=False, nullable=False)
    outlier_data = Column(Boolean, default=True, nullable=False)
    force_true = Column(Boolean, default=False, nullable=False)
    
    # Relacionamento
    job = relationship("Job", back_populates="job_data")

class QueryLog(Base):
    __tablename__ = "query_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    job_name = Column(String, nullable=False)
    job_filename = Column(String, nullable=False)
    attributes = Column(JSON, nullable=True)
    result = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    referer = Column(String, nullable=True)
    fingerprint = Column(String, nullable=False)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone(os.getenv("TZ", "America/Sao_Paulo"))), nullable=False)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    monai_history_executions = Column(Integer, nullable=False)
    force_true = Column(Boolean, default=False, nullable=False)
    use_historical_outlier = Column(Boolean, default=False, nullable=False)
    
    # Relacionamento
    job = relationship("Job", back_populates="query_logs")
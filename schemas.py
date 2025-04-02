from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime
import hashlib

class JobBase(BaseModel):
    job_name: str = Field(..., description="Nome do job.")
    job_filename: str = Field(..., description="Nome do arquivo do job.")
    description: Optional[str] = Field(None, description="Descrição do job.")
    is_active: bool = Field(True, description="Indica se o job está ativo.")

class JobCreate(JobBase):
    pass

class JobUpdate(JobBase):
    job_name: Optional[str] = None
    job_filename: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Job(JobBase):
    id: str = Field(..., description="Identificador único do job (SHA-256 do nome e arquivo).")
    created_at: datetime = Field(..., description="Data e hora de criação do job.")
    updated_at: datetime = Field(..., description="Data e hora da última atualização do job.")

    class Config:
        from_attributes = True

class JobDataCreate(BaseModel):
    job_name: str = Field(..., description="Nome do job.")
    job_filename: str = Field(..., description="Nome do arquivo do job.")
    attributes: Dict[str, str] = Field(
        ..., 
        description="Atributos do job, representados como um dicionário de chave-valor."
    )
    monai_history_executions: int = Field(
        ..., 
        gt=0, 
        description="Número de execuções históricas a serem consideradas para análise. Deve ser maior que 0."
    )
    outlier_data: Optional[bool] = Field(
        default=True,
        description="Indica se os dados enviados são considerados outliers."
    )
    use_historical_outlier: Optional[bool] = Field(
        default=False,
        description="Força a utilização de outlier no histórico."
    )
    force_true: Optional[bool] = Field(
        default=False,
        description="Força o resultado como True, ignorando a análise."
    )

    @property
    def job_id(self) -> str:
        """Gera um identificador único para o job baseado no nome e nome do arquivo."""
        raw_id = f"{self.job_name}-{self.job_filename}"
        return hashlib.sha256(raw_id.encode()).hexdigest()

class JobDataResponse(BaseModel):
    id: UUID = Field(..., description="Identificador único do registro no banco de dados.")
    job_id: str = Field(..., description="Identificador único do job (SHA-256 do nome e arquivo).")
    job_name: str = Field(..., description="Nome do job.")
    job_filename: str = Field(..., description="Nome do arquivo do job.")
    attributes: Dict[str, str] = Field(..., description="Atributos do job, representados como um dicionário de chave-valor.")
    received_at: datetime = Field(..., description="Data e hora em que o registro foi recebido.")
    weekday: str = Field(..., description="Dia da semana em que o registro foi recebido (ex.: 'Monday', 'Tuesday').")
    month: str = Field(..., description="Mês em que o registro foi recebido (ex.: 'January', 'February').")
    is_holiday: bool = Field(..., description="Indica se o dia do registro é um feriado.")
    outlier_data: bool = Field(..., description="Indica se o registro é considerado um outlier com base na análise.")
    use_historical_outlier: bool = Field(default=False, description="Indica se o registro foi forçado a considerar outliers no histórico.")
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from uuid import UUID
from datetime import datetime
import hashlib

# Primeiro definimos as classes base e regras
class RuleBase(BaseModel):
    name: str = Field(..., description="Nome da regra.")
    description: Optional[str] = Field(None, description="Descrição da regra.")
    rule_text: str = Field(..., description="Texto da regra.")
    is_active: bool = Field(True, description="Indica se a regra está ativa.")

class RuleCreate(RuleBase):
    pass

class RuleUpdate(RuleBase):
    name: Optional[str] = None
    description: Optional[str] = None
    rule_text: Optional[str] = None
    is_active: Optional[bool] = None

class Rule(RuleBase):
    id: UUID = Field(..., description="Identificador único da regra.")
    created_at: datetime = Field(..., description="Data e hora de criação da regra.")
    updated_at: datetime = Field(..., description="Data e hora da última atualização da regra.")

    class Config:
        from_attributes = True

# Depois definimos as classes de grupos de regras
class RuleGroupBase(BaseModel):
    name: str = Field(..., description="Nome do grupo de regras.")
    description: Optional[str] = Field(None, description="Descrição do grupo de regras.")
    is_active: bool = Field(True, description="Indica se o grupo de regras está ativo.")

class RuleGroupCreate(RuleGroupBase):
    rule_ids: List[UUID] = Field(..., min_items=1, description="Lista de IDs das regras que compõem o grupo. Deve conter pelo menos uma regra.")

class RuleGroupUpdate(RuleGroupBase):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    rule_ids: Optional[List[UUID]] = Field(None, min_items=1, description="Lista de IDs das regras que compõem o grupo. Deve conter pelo menos uma regra.")

class RuleGroup(RuleGroupBase):
    id: UUID = Field(..., description="Identificador único do grupo de regras.")
    created_at: datetime = Field(..., description="Data e hora de criação do grupo de regras.")
    updated_at: datetime = Field(..., description="Data e hora da última atualização do grupo de regras.")
    rules: List[Rule] = Field(..., min_items=1, description="Lista de regras que compõem o grupo. Deve conter pelo menos uma regra.")

    class Config:
        from_attributes = True

# Agora podemos atualizar a classe Rule para incluir o relacionamento com grupos
class RuleWithGroups(Rule):
    rule_groups: List[RuleGroup] = Field(default_factory=list, description="Grupos de regras aos quais esta regra pertence.")

# Por fim, definimos as classes relacionadas a jobs
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
    rule_group_ids: Optional[List[UUID]] = None

class Job(JobBase):
    id: str = Field(..., description="Identificador único do job (SHA-256 do nome e arquivo).")
    created_at: datetime = Field(..., description="Data e hora de criação do job.")
    updated_at: datetime = Field(..., description="Data e hora da última atualização do job.")
    rule_groups: List[RuleGroup] = Field(default_factory=list, description="Grupos de regras associados ao job.")

    class Config:
        from_attributes = True

class JobDataCreate(BaseModel):
    job_name: str = Field(..., description="Nome do job.")
    job_filename: str = Field(..., description="Nome do arquivo do job.")
    attributes: Dict[str, Any] = Field(..., description="Atributos do job.")
    monai_history_executions: Optional[int] = Field(None, description="Número de execuções históricas a serem consideradas.")
    use_historical_outlier: Optional[bool] = Field(False, description="Indica se deve considerar outliers no histórico.")
    force_true: Optional[bool] = Field(False, description="Indica se deve forçar o resultado como true.")

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
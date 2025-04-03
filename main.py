import os
from fastapi import FastAPI, HTTPException, Request, Depends, APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends
from database import SessionLocal, engine
from models import Base, JobData, QueryLog, Job, Rule, RuleGroup
from schemas import (
    JobDataCreate, JobDataResponse, JobCreate, JobUpdate, Job as JobSchema,
    RuleCreate, RuleUpdate, RuleWithGroups as RuleSchema,
    RuleGroupCreate, RuleGroupUpdate, RuleGroup as RuleGroupSchema
)
import uuid
from uuid import UUID  # Adicionando a importação do tipo UUID
from datetime import datetime, timedelta
import holidays
from typing import Union, List
import json
import pytz  # Biblioteca para lidar com timezones
from llm_client import initialize_llm_client, send_prompt_to_llm
import hashlib  # Import necessário para gerar o fingerprint
from fastapi.responses import JSONResponse

# Verificar e criar tabelas no banco de dados 
def create_tables():
    print("Verificando e criando tabelas no banco de dados, se necessário")
    Base.metadata.create_all(bind=engine)

# Inicializar a aplicação FastAPI com informações personalizadas
app = FastAPI(
    title="MonAI API",
    description="""
    MonAI é uma aplicação para detecção de anomalias em entregas recorrentes de arquivos de dados.
    
    ## Funcionalidades:
    - **Jobs**: Gerenciamento de jobs (CRUD).
    - **Regras**: Gerenciamento de regras mandatórias associadas aos jobs.
    - **Dashboard**: Visualização de consultas e detecção de anomalias.
    - **Administração**: Recriação de tabelas e gerenciamento de usuários.

    Explore os endpoints abaixo para interagir com a API.
    """,
    version="1.0.0",
    contact={
        "name": "Equipe MonAI",
        "email": "suporte@monai.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Criar router para a versão 1 da API
api_v1 = APIRouter(prefix="/api/v1")

# Chamar a função para verificar e criar tabelas
create_tables()

# Configurar timezone
def get_timezone():
    tz_name = os.getenv("TZ", "America/Sao_Paulo")  # Padrão: America/Sao_Paulo
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Timezone inválido: {tz_name}")

timezone = get_timezone()

# Função para obter o horário atual ajustado para o timezone configurado
def get_current_time():
    return datetime.now()

# Configuração do cliente LLM
client, llm_model, llm_provider = initialize_llm_client()

# Configuração de variáveis de ambiente
HISTORY_EXECUTIONS = int(os.getenv("MONAI_HISTORY_EXECUTIONS", 30))  # Padrão: 30 execuções
MAX_TOKENS = int(os.getenv("MONAI_MAX_TOKENS", 200))  # Padrão: 200 tokens

# Dependency para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_job(db: Session, job_name: str, job_filename: str, description: str = None) -> Job:
    """
    Verifica se um job existe e o retorna, ou cria um novo se não existir.
    
    Args:
        db (Session): Sessão do banco de dados
        job_name (str): Nome do job
        job_filename (str): Nome do arquivo do job
        description (str, optional): Descrição do job
        
    Returns:
        Job: O job existente ou recém-criado
    """
    # Gerar o job_id
    raw_id = f"{job_name}-{job_filename}"
    job_id = hashlib.sha256(raw_id.encode()).hexdigest()
    
    # Verificar se o job existe
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        # Criar novo job
        job = Job(
            id=job_id,
            job_name=job_name,
            job_filename=job_filename,
            description=description,
            is_active=True
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    
    return job

def clean_response(response: str) -> str:
    """
    Remove caracteres desnecessários, como backticks e texto adicional,
    para garantir que a resposta seja um JSON puro.
    """
    response = response.strip()  # Remove espaços em branco no início e no final
    response = response.strip("```json").strip("```")
    if response.startswith("```json"):
        response = response[7:].strip()  # Remove os 3 backticks e json no início
    if response.startswith("```"):
        response = response[3:].strip()  # Remove os 3 backticks no início
    if response.endswith("```"):
        response = response[3:].strip()  # Remove os 3 backticks no no final
    if response.startswith("json"):
        response = response[4:].strip()  # Remove o prefixo "json" se existir

    """
    Remove tudo que estiver antes do primeiro '{' e depois do último '}'.
    Garante que a resposta seja um JSON puro.
    """
    try:
        # Localiza o índice do primeiro '{' e do último '}'
        start_index = response.index('{')
        end_index = response.rindex('}') + 1  # Inclui o último '}'

        # Retorna apenas o conteúdo entre o primeiro '{' e o último '}'
        return response[start_index:end_index].strip()
    except ValueError:
        # Caso não encontre '{' ou '}', retorna um erro
        raise ValueError("A resposta não contém um JSON válido.")

def log_query(
    db: Session,
    job_id: str,
    job_name: str,
    job_filename: str,
    attributes: dict,
    result: str,
    explanation: str,
    ip_address: str,
    user_agent: str,
    referer: str,
    received_at: datetime,
    monai_history_executions: int,
    force_true: bool = False
):
    """
    Função para registrar informações no QueryLog.

    Args:
        db (Session): Sessão do banco de dados.
        job_id (str): ID do job (SHA-256).
        job_name (str): Nome do job.
        job_filename (str): Nome do arquivo do job.
        attributes (dict): Atributos do job.
        result (str): Resultado da análise.
        explanation (str): Explicação do resultado.
        ip_address (str): Endereço IP do cliente.
        user_agent (str): User-Agent do cliente.
        referer (str): Referer do cliente.
        received_at (datetime): Data e hora do registro.
        monai_history_executions (int): Número de execuções históricas consideradas.
    """
    # Criar fingerprint único
    raw_fingerprint = f"{ip_address}-{user_agent}-{referer}"
    fingerprint = hashlib.sha256(raw_fingerprint.encode()).hexdigest()

    # Criar o registro no QueryLog
    query_log = QueryLog(
        job_id=job_id,
        job_name=job_name,
        job_filename=job_filename,
        attributes=attributes,
        result=result,
        explanation=explanation,
        referer=referer,
        fingerprint=fingerprint,
        received_at=received_at,
        ip_address=ip_address,
        monai_history_executions=monai_history_executions
    )
    db.add(query_log)
    db.commit()

def get_job_rules(db: Session, job_id: str) -> List[str]:
    """
    Obtém todas as regras ativas associadas a um job através de seus grupos de regras.
    
    Args:
        db (Session): Sessão do banco de dados
        job_id (str): ID do job
        
    Returns:
        List[str]: Lista de regras ativas
    """
    # Buscar o job com seus grupos de regras
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return []
    
    # Coletar todas as regras ativas dos grupos ativos
    rules = set()
    for group in job.rule_groups:
        if group.is_active:
            for rule in group.rules:
                if rule.is_active:
                    rules.add(rule.rule_text)
    
    return list(rules)

# Endpoints para gerenciamento de regras
@api_v1.post("/rules/", response_model=RuleSchema, tags=["Regras"])
async def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova regra.
    """
    db_rule = Rule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@api_v1.get("/rules/", response_model=List[RuleSchema], tags=["Regras"])
async def list_rules(db: Session = Depends(get_db)):
    """
    Lista todas as regras cadastradas.
    """
    return db.query(Rule).all()

@api_v1.get("/rules/{rule_id}", response_model=RuleSchema, tags=["Regras"])
async def get_rule(rule_id: UUID, db: Session = Depends(get_db)):
    """
    Obtém informações de uma regra específica.
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    return rule

@api_v1.put("/rules/{rule_id}", response_model=RuleSchema, tags=["Regras"])
async def update_rule(rule_id: UUID, rule_update: RuleUpdate, db: Session = Depends(get_db)):
    """
    Atualiza informações de uma regra existente.
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    
    update_data = rule_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    return rule

@api_v1.delete("/rules/{rule_id}", tags=["Regras"])
async def delete_rule(rule_id: UUID, db: Session = Depends(get_db)):
    """
    Remove uma regra do sistema.
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    
    db.delete(rule)
    db.commit()
    return {"message": "Regra removida com sucesso."}

# Endpoints para gerenciamento de grupos de regras
@api_v1.post("/rule-groups/", response_model=RuleGroupSchema, tags=["Grupos de Regras"])
async def create_rule_group(group: RuleGroupCreate, db: Session = Depends(get_db)):
    """
    Cria um novo grupo de regras.
    """
    # Verifica se todas as regras existem e estão ativas
    rules = db.query(Rule).filter(Rule.id.in_(group.rule_ids), Rule.is_active == True).all()
    if len(rules) != len(group.rule_ids):
        raise HTTPException(
            status_code=400,
            detail="Uma ou mais regras não foram encontradas ou não estão ativas."
        )

    # Cria o grupo de regras
    db_group = RuleGroup(
        name=group.name,
        description=group.description,
        is_active=group.is_active
    )
    db_group.rules = rules
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@api_v1.get("/rule-groups/", response_model=List[RuleGroupSchema], tags=["Grupos de Regras"])
async def list_rule_groups(db: Session = Depends(get_db)):
    """
    Lista todos os grupos de regras cadastrados.
    """
    return db.query(RuleGroup).all()

@api_v1.get("/rule-groups/{group_id}", response_model=RuleGroupSchema, tags=["Grupos de Regras"])
async def get_rule_group(group_id: UUID, db: Session = Depends(get_db)):
    """
    Obtém informações de um grupo de regras específico.
    """
    group = db.query(RuleGroup).filter(RuleGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo de regras não encontrado.")
    return group

@api_v1.put("/rule-groups/{group_id}", response_model=RuleGroupSchema, tags=["Grupos de Regras"])
async def update_rule_group(group_id: UUID, group_update: RuleGroupUpdate, db: Session = Depends(get_db)):
    """
    Atualiza informações de um grupo de regras existente.
    """
    group = db.query(RuleGroup).filter(RuleGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo de regras não encontrado.")
    
    update_data = group_update.dict(exclude_unset=True)
    
    # Se estiver atualizando as regras, verifica se todas existem e estão ativas
    if "rule_ids" in update_data:
        rules = db.query(Rule).filter(Rule.id.in_(update_data["rule_ids"]), Rule.is_active == True).all()
        if len(rules) != len(update_data["rule_ids"]):
            raise HTTPException(
                status_code=400,
                detail="Uma ou mais regras não foram encontradas ou não estão ativas."
            )
        group.rules = rules
        del update_data["rule_ids"]
    
    # Atualiza os demais campos
    for field, value in update_data.items():
        setattr(group, field, value)
    
    db.commit()
    db.refresh(group)
    return group

@api_v1.delete("/rule-groups/{group_id}", tags=["Grupos de Regras"])
async def delete_rule_group(group_id: UUID, db: Session = Depends(get_db)):
    """
    Remove um grupo de regras do sistema.
    """
    group = db.query(RuleGroup).filter(RuleGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo de regras não encontrado.")
    
    db.delete(group)
    db.commit()
    return {"message": "Grupo de regras removido com sucesso."}

# Endpoint para criar um novo job
@api_v1.post("/jobs/create/", response_model=JobSchema, tags=["Jobs"])
async def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """
    Cria um novo job.
    """
    # Gerar o job_id
    raw_id = f"{job.job_name}-{job.job_filename}"
    job_id = hashlib.sha256(raw_id.encode()).hexdigest()
    
    # Verificar se o job já existe
    if db.query(Job).filter(Job.id == job_id).first():
        raise HTTPException(status_code=400, detail="Job já existe.")
    
    # Criar o job
    db_job = Job(
        id=job_id,
        job_name=job.job_name,
        job_filename=job.job_filename,
        description=job.description,
        is_active=job.is_active
    )
    
    # Adicionar grupos de regras se fornecidos
    if hasattr(job, "rule_group_ids") and job.rule_group_ids:
        rule_groups = db.query(RuleGroup).filter(
            RuleGroup.id.in_(job.rule_group_ids),
            RuleGroup.is_active == True
        ).all()
        if len(rule_groups) != len(job.rule_group_ids):
            raise HTTPException(status_code=400, detail="Um ou mais grupos de regras não foram encontrados ou estão inativos.")
        db_job.rule_groups = rule_groups
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

# Endpoint para registrar dados de um job
@api_v1.post("/jobs/data/", response_model=Union[JobDataResponse, dict], tags=["Jobs"])
async def create_job_data(job_data: JobDataCreate, request: Request, db: Session = Depends(get_db)):
    try:
        # Verificar ou criar o job automaticamente
        job = get_or_create_job(db, job_data.job_name, job_data.job_filename)
        
        if not job.is_active:
            raise HTTPException(status_code=400, detail="O job está inativo.")

        # Obter o horário atual no timezone configurado
        now = get_current_time()
        weekday = now.strftime("%A")  # Dia da semana
        month = now.strftime("%B")  # Nome do mês
        br_holidays = holidays.Brazil()
        is_holiday = now.date() in br_holidays

        # Informações da origem da request para registrar a consulta no QueryLog
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "unknown")
        referer = request.headers.get("referer", "unknown")
        
        # Determinar o número de execuções de histórico
        history_executions = (
            job_data.monai_history_executions
            or int(os.getenv("MONAI_HISTORY_EXECUTIONS", 30))
        )

        if history_executions <= 0:
            raise ValueError("O número de histórico de execuções deve ser maior que zero.")

        # Consultar os registros mais recentes com base no número de execuções
        if job_data.use_historical_outlier:
            historical_data = db.query(JobData).filter(
                JobData.job_id == job.id
            ).order_by(JobData.received_at.desc()).limit(history_executions).all()
        else:
            historical_data = db.query(JobData).filter(
                JobData.job_id == job.id,
                JobData.outlier_data == False
            ).order_by(JobData.received_at.desc()).limit(history_executions).all()

        if len(historical_data) >= history_executions:
            # Preparar os dados para enviar ao LLM
            historical_attributes = [
                {
                    "attributes": data.attributes,
                    "received_at": data.received_at,
                    "weekday": data.weekday,
                    "month": data.month,
                    "is_holiday": data.is_holiday
                }
                for data in historical_data
            ]

            # Regra padrão que sempre deve ser aplicada
            DEFAULT_RULE = "Considere as variações contextuais e os padrões esperados, dando maior relevância aos dados históricos mais recentes."
            
            # Buscar as regras associadas ao job
            rules_from_job = get_job_rules(db, job.id)
            
            # Combinar a regra padrão com as regras do job
            rules = [DEFAULT_RULE] + (rules_from_job if rules_from_job else [])

            # Formatar as regras para o prompt
            mandatory_rules = "".join(f"{i + 1}. {rule}\n" for i, rule in enumerate(rules))

            prompt = (
                "Contexto: Você é a maior autoridade em qualidade de dados, reconhecida por sua expertise em identificar padrões e inconsistências com precisão. "
                "Com anos de experiência aprofundada, você domina técnicas avançadas de análise e possui um olhar crítico para avaliar a confiabilidade e a coerência dos dados em qualquer cenário.\n"
                "Papel: Analista de qualidade de dados altamente especializada, referência na área.\n"
                "Objetivo: Sua missão é garantir a integridade e a consistência dos metadados de arquivos enviados periodicamente. Além de validar a lógica entre os dados recedidos no último conjunto de metadados, "
                "você analisará o histórico de metadados de remessas anteriores, aplicando, dentre outras técnicas, técnicas avançadas como: \n"
                "- Análise Exploratória de Dados (EDA) para identificar propriedades estatísticas e padrões históricos.\n"
                "- Detecção de Anomalias utilizando métodos estatísticos, modelagem probabilística e algoritmos de machine learning.\n"
                "- Análise de Séries Temporais para compreender tendências, sazonalidades e variações estruturais nos metadados.\n"
                "- Regras de Negócio e Modelos Heurísticos para identificar desvios esperados e não esperados nos dados.\n"
                "Além disso, você deve garantir que nenhuma regra obrigatória seja violada, assegurando que os dados estejam em conformidade com os requisitos estabelecidos.\n"
                "Entre as informações disponíveis, constam o dia da semana e o mês e de geração das remessas, também indicando se no dia da geração é um feriado. Essas variáveis são fundamentais para a análise, "
                "pois os metadados podem variar conforme o contexto temporal. Sua avaliação deve considerar a periodicidade e essas particularidades para distinguir padrões legítimos de possíveis anomalias, "
                "garantindo um alto padrão de qualidade e confiabilidade nos dados.\n\n"
                "As regras abaixo são obrigatórias para a análise e resultado:\n"
                f"{mandatory_rules}\n"
                "\n"
                f"Histórico de dados das últimas {history_executions} execuções:\n{historical_attributes}\n\n"
                f"Último conjunto de metadados recebido: \n{job_data.attributes}\nRecebido em: {now}\nDia da semana: {weekday}\nMês: {month}\nFeriado: {is_holiday}\n\n"
                "Saída esperada: Com base na análise, responda de forma objetiva, resumida e direta com uma das seguintes opções:\n"
                "'true': Se o novo dado segue o mesmo padrão do histórico fornecido.\n"
                "'false': Se o novo dado apresenta um padrão incomum dentro do histórico.\n"
                "A resposta deve obrigatoriamente ser formatada em tipo de conterúdo JSON (Content-Type: application/json), contendo uma chave com o resultado da análise (true/false) e uma chave com a explicação resumida. Exemplo:\n"
                "{\n"
                "  \"result\": \"false\",\n"
                "  \"explain\": \"O novo dado apresenta uma anomalia significativa em seu valor de 'max', que é consideravelmente mais alto que os valores históricos...\"\n"
                "}\n"
                "Retorne exclusivamente o conteúdo JSON solicitado, sem adicionar qualquer informação extra ou caracteres adicionais, pois a resposta será importada diretamente como JSON puro em outro sistema."
            )

            print(prompt)

            # Enviar o prompt ao LLM
            evaluation = send_prompt_to_llm(client, llm_model, llm_provider, prompt, max_tokens=MAX_TOKENS)

            # Limpar e processar a resposta
            evaluation = clean_response(evaluation)
            evaluation = json.loads(evaluation)

            # Verificar se as chaves esperadas estão presentes
            if "result" not in evaluation or "explain" not in evaluation:
                raise ValueError("A resposta do modelo não contém as chaves esperadas: 'result' e 'explain'.")

            # Processar o resultado com base no valor de 'result'
            result = evaluation["result"].lower()
            explanation = evaluation["explain"]

            if job_data.force_true:
                result = "true"
                explanation = "Resultado forçado como 'true' devido à configuração do job: " + explanation
            
            # Registrar a consulta no QueryLog
            log_query(
                db=db,
                job_id=job.id,
                job_name=job.job_name,
                job_filename=job.job_filename,
                attributes=job_data.attributes,
                result=result,
                explanation=explanation,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                received_at=now,
                monai_history_executions=history_executions,
                force_true=job_data.force_true                
            )

            # Criar novo registro no banco de dados
            new_job_data = JobData(
                id=uuid.uuid4(),
                job_id=job.id,
                job_name=job.job_name,
                job_filename=job.job_filename,
                attributes=job_data.attributes,
                received_at=now,
                weekday=weekday,
                month=month,
                is_holiday=is_holiday,
                outlier_data=(result != "true"),
                force_true=job_data.force_true
            )
            db.add(new_job_data)
            db.commit()
            db.refresh(new_job_data)
            
            if result == "true":
                return {"result": result, "explanation": explanation}
            elif result == "false":
                raise HTTPException(status_code=400, detail={"result": result, "explanation": explanation})
            else:
                raise ValueError("O valor de 'result' na resposta do modelo é inválido.")
        else:
            # Criar novo registro no banco de dados
            new_job_data = JobData(
                id=uuid.uuid4(),
                job_id=job.id,
                job_name=job.job_name,
                job_filename=job.job_filename,
                attributes=job_data.attributes,
                received_at=now,
                weekday=weekday,
                month=month,
                is_holiday=is_holiday,
                outlier_data=False,
                force_true=job_data.force_true
            )
            db.add(new_job_data)
            db.commit()
            db.refresh(new_job_data)

            # Registrar a consulta no QueryLog
            log_query(
                db=db,
                job_id=job.id,
                job_name=job.job_name,
                job_filename=job.job_filename,
                attributes=job_data.attributes,
                result="null",
                explanation=f"É necessário pelo menos {history_executions} execuções de dados históricos para avaliação, mas apenas {len(historical_data)} estão disponíveis.",
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                received_at=now,
                monai_history_executions=history_executions,
                force_true=job_data.force_true
            )
            return {"message": f"É necessário pelo menos {history_executions} execuções de dados históricos para avaliação, mas apenas {len(historical_data)} estão disponíveis."}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_v1.get("/jobs/", response_model=List[JobSchema], tags=["Jobs"])
async def list_jobs(db: Session = Depends(get_db)):
    """
    Lista todos os jobs cadastrados.
    """
    return db.query(Job).all()

@api_v1.get("/jobs/{job_id}", response_model=JobSchema, tags=["Jobs"])
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    Obtém informações de um job específico.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return job

@api_v1.delete("/jobs/{job_id}", tags=["Jobs"])
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """
    Remove um job do sistema.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    
    db.delete(job)
    db.commit()
    return {"message": "Job removido com sucesso."}

@api_v1.post("/recreate-tables/", tags=["Administração"])
async def recreate_tables(db: Session = Depends(get_db)):
    """
    Endpoint para recriar as tabelas no banco de dados.
    Remove todas as tabelas existentes e as recria em branco.
    """
    try:
        Base.metadata.drop_all(bind=engine)  # Remove todas as tabelas
        Base.metadata.create_all(bind=engine)  # Recria as tabelas
        return JSONResponse(content={"message": "Tabelas recriadas com sucesso."}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recriar tabelas: {str(e)}")

# Incluir o router da API v1 na aplicação principal
app.include_router(api_v1)
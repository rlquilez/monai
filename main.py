import os
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi import Depends
from database import SessionLocal, engine
from models import Base, JobData, QueryLog
from schemas import JobDataCreate, JobDataResponse
import uuid
from datetime import datetime, timedelta
import holidays
from typing import Union
import json
import pytz  # Biblioteca para lidar com timezones
from llm_client import initialize_llm_client, send_prompt_to_llm
import hashlib  # Import necessário para gerar o fingerprint

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
    now_utc = datetime.utcnow()
    return now_utc.astimezone(timezone)

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
    attributes: dict,
    result: str,
    explanation: str,
    ip_address: str,
    user_agent: str,
    referer: str,
    received_at: datetime,
    monai_history_executions: int
):
    """
    Função para registrar informações no QueryLog.

    Args:
        db (Session): Sessão do banco de dados.
        job_id (str): ID do job.
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

@app.post("/jobs/", response_model=Union[JobDataResponse, dict], tags=["Jobs"])
async def create_job_data(job_data: JobDataCreate, request: Request, db: Session = Depends(get_db)):
    try:
        # Obter o horário atual no timezone configurado
        now = get_current_time()  # Já retorna no timezone America/Sao_Paulo
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
        historical_data = db.query(JobData).filter(
            JobData.job_id == job_data.job_id
        ).order_by(JobData.received_at.desc()).limit(history_executions).all()

        # Criar novo registro no banco de dados
        new_job_data = JobData(
            id=uuid.uuid4(),
            job_id=job_data.job_id,
            attributes=job_data.attributes,
            received_at=now,  # Armazena o horário no timezone America/Sao_Paulo
            weekday=weekday,
            month=month,
            is_holiday=is_holiday
        )
        db.add(new_job_data)
        db.commit()
        db.refresh(new_job_data)

        if len(historical_data) < history_executions:
            log_query(
                db=db,
                job_id=str(job_data.job_id),
                attributes=job_data.attributes,
                result="null",
                explanation=f"É necessário pelo menos {history_executions} execuções de dados históricos para avaliação, mas apenas {len(historical_data)} estão disponíveis.",
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                received_at=now,
                monai_history_executions=history_executions
            )
            return {"message": f"É necessário pelo menos {history_executions} execuções de dados históricos para avaliação, mas apenas {len(historical_data)} estão disponíveis."}

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

        rules = [
            "Considere as variações contextuais e os padrões esperados, dando maior relevância aos dados históricos mais recentes."
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'avg', juntamente com 'min' e 'max', o valor de 'avg' deve estar dentro do intervalo definido pelos valores de 'min' e 'max'."
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'mean', juntamente com 'min' e 'max', o valor de 'mean' deve estar dentro do intervalo definido pelos valores de 'min' e 'max'.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'max', o valor de 'max' deve ser maior que o valor de 'min'.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'std', juntamente com 'min' e 'max', o valor de 'std' deve ser menor que a diferença entre os valores de 'max' e 'min'.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'stdev', juntamente com 'min' e 'max', o valor de 'stdev' deve ser menor que a diferença entre os valores de 'max' e 'min'.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'count', o valor de 'count' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'sum', o valor de 'sum' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'median', o valor de 'median' deve estar entre os valores de 'min' e 'max'.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'mode', o valor de 'mode' deve estar entre os valores de 'min' e 'max'.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'variance', o valor de 'variance' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'skewness', o valor de 'skewness' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'kurtosis', o valor de 'kurtosis' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'range', o valor de 'range' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'iqr', o valor de 'iqr' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'mad', o valor de 'mad' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'cv', o valor de 'cv' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'z_score', o valor de 'z_score' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'p_value', o valor de 'p_value' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'confidence_interval', o valor de 'confidence_interval' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'upper_bound', o valor de 'upper_bound' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'lower_bound', o valor de 'lower_bound' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'outliers', o valor de 'outliers' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'percentiles', o valor de 'percentiles' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'deciles', o valor de 'deciles' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'quartiles', o valor de 'quartiles' deve ser maior que zero.",
            "Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'deciles', o valor de 'deciles' deve ser maior que zero.",
        ]

        # Adicionar regras adicionais para cada cenários de dados

        mandatory_rules = "".join([f"{i + 1}. {rule}\n" for i, rule in enumerate(rules)])

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
            "A resposta deve obrigatoriamente ser formatada em JSON, contendo uma chave com o resultado da análise (true/false) e uma chave com a explicação resumida. Exemplo:\n"
            "{\n"
            "  \"result\": \"false\",\n"
            "  \"explain\": \"O novo dado apresenta uma anomalia significativa em seu valor de 'max', que é consideravelmente mais alto que os valores históricos...\"\n"
            "}\n"
            "Retorne exclusivamente o conteúdo JSON solicitado, sem adicionar qualquer informação extra ou caracteres adicionais, pois a resposta será importada diretamente como JSON puro em outro sistema."
        )

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

        log_query(
            db=db,
            job_id=str(job_data.job_id),
            attributes=job_data.attributes,
            result=result,
            explanation=explanation,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            received_at=now,
            monai_history_executions=history_executions
        )
        
        if result == "true":
            return {"result": result, "explanation": explanation}
        elif result == "false":
            raise HTTPException(status_code=400, detail={"result": result, "explanation": explanation})
        else:
            raise ValueError("O valor de 'result' na resposta do modelo é inválido.")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/recreate-tables/", tags=["Administração"])
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
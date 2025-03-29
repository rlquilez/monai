import os
from fastapi import FastAPI, HTTPException, Request, Depends, Form
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, JobData, QueryLog
from schemas import JobDataCreate, JobDataResponse
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import pytz
import holidays
import uuid
import json
import requests
import time
import random
from typing import Union
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Inicializar a aplicação FastAPI com informações personalizadas
app = FastAPI(
    title="MonAI API.",
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
        "email": "rodrigo@quilez.com.br",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Substitua "*" por uma lista de origens específicas, se necessário.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar timezone
def get_timezone():
    tz_name = os.getenv("TZ", "UTC")
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Timezone inválido: {tz_name}")

timezone = get_timezone()

def get_current_time():
    """
    Retorna o horário atual no timezone configurado.
    """
    return datetime.now(timezone)

# Verificar e criar tabelas no banco de dados
def create_tables():
    print("Verificando e criando tabelas no banco de dados, se necessário")
    Base.metadata.create_all(bind=engine)

# Chamar a função para verificar e criar tabelas
create_tables()

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


@app.post("/jobs/", response_model=Union[JobDataResponse, dict], tags=["Jobs"])
async def create_job_data(job_data: JobDataCreate, request: Request, db: Session = Depends(get_db)):
    try:
        # Obter o horário atual no timezone configurado
        now = get_current_time()
        weekday = now.strftime("%A")
        br_holidays = holidays.Brazil()
        is_holiday = now.date() in br_holidays

        # Determinar o número de dias de histórico
        history_days = (
            job_data.monai_history_days  # 1. Valor enviado na requisição
            or int(os.getenv("MONAI_HISTORY_DAYS", 30))  # 2. Variável de ambiente
        )

        if history_days <= 0:
            raise ValueError("O número de dias de histórico deve ser maior que zero.")

        # Consultar dados históricos com base no número de dias configurado e na coluna received_at
        start_date = now - timedelta(days=history_days)
        start_date_utc = start_date.astimezone(pytz.utc)

        historical_data = db.query(JobData).filter(
            JobData.job_id == job_data.job_id,
            JobData.received_at >= start_date_utc
        ).order_by(JobData.received_at.desc()).all()

        # Criar novo registro no banco de dados
        new_job_data = JobData(
            id=uuid.uuid4(),
            job_id=job_data.job_id,
            attributes=job_data.attributes,
            received_at=now,  # Já ajustado para o timezone configurado
            weekday=weekday,
            is_holiday=is_holiday
        )
        db.add(new_job_data)
        db.commit()
        db.refresh(new_job_data)

        if len(historical_data) < history_days:
            return {"message": f"É necessário pelo menos {history_days} dias de dados históricos para avaliação, mas apenas {len(historical_data)} dias estão disponíveis."}

        # Preparar os dados para enviar ao LLM
        historical_attributes = [
            {
                "attributes": data.attributes,
                "received_at": data.received_at,
                "weekday": data.weekday,
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
            "Entre as informações disponíveis, constam o dia da semana de geração das remessas e a indicação de feriados. Essas variáveis são fundamentais para a análise, "
            "pois os metadados podem variar conforme o contexto temporal. Sua avaliação deve considerar essas particularidades para distinguir padrões legítimos de possíveis anomalias, "
            "garantindo um alto padrão de qualidade e confiabilidade nos dados.\n\n"
            "As regras abaixo são obrigatórias para a análise e resultado:\n"
            f"{mandatory_rules}\n"
            "\n"
            f"Histórico de dados dos últimos {history_days} dias:\n{historical_attributes}\n\n"
            f"Último conjunto de metadados recebido: \n{job_data.attributes}\nRecebido em: {now}\nDia da semana: {weekday}\nFeriado: {is_holiday}\n\n"
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

        #print(prompt)

        # Chamada ao LLM com base no provedor configurado
        if os.getenv("MONAI_LLM", "OPENAI").upper() == 'OPENAI':
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": "Você é um analista de qualidade de dados altamente especializado."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=0
            )
        elif os.getenv("MONAI_LLM", "OPENAI").upper() == 'GOOGLE':
            from google.genai import types
            response = client.models.generate_content(
                model=llm_model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction="Você é um analista de qualidade de dados altamente especializado.",
                    #max_output_tokens=MAX_TOKENS,
                    temperature=0
                )
            )
        elif os.getenv("MONAI_LLM", "OPENAI").upper() == 'ANTHROPIC':
            response = client.messages.create(
                model=llm_model,
                system="Você é um analista de qualidade de dados altamente especializado. Sua tarefa é avaliar minuciosamente se os dados fornecidos seguem o mesmo padrão ou se há alguma anomalia.",
                max_tokens=MAX_TOKENS,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        else:
            raise ValueError("Cliente LLM não suportado.")

        # Obter a resposta do modelo
        if os.getenv("MONAI_LLM", "OPENAI").upper() == 'OPENAI':
            evaluation = response.choices[0].message.content.strip()
        elif os.getenv("MONAI_LLM", "OPENAI").upper() == 'GOOGLE':
            evaluation = getattr(response, "text", "").strip()
        elif os.getenv("MONAI_LLM", "OPENAI").upper() == 'ANTHROPIC':
            evaluation = getattr(response.content[0], "text", "").strip()
        else:
            raise ValueError("Cliente LLM não suportado.")

        # Verificar se a resposta está vazia
        if not evaluation:
            raise HTTPException(status_code=500, detail="A resposta do modelo está vazia ou inválida.")

        # Limpar a resposta para garantir que seja um JSON puro
        #print('Antes limpeza:', evaluation)
        evaluation = clean_response(evaluation)
        #print('Depois limpeza:', evaluation)

        # Avaliar a resposta do modelo
        try:
            evaluation = json.loads(evaluation)  # Tentar interpretar a resposta como JSON
            
            # Verificar se as chaves esperadas estão presentes
            if "result" not in evaluation or "explain" not in evaluation:
                raise ValueError("A resposta do modelo não contém as chaves esperadas: 'result' e 'explain'.")

            # Processar o resultado com base no valor de 'result'
            result = evaluation["result"].lower()
            explanation = evaluation["explain"]

        except json.JSONDecodeError:
            # Caso a resposta não seja um JSON válido
            raise HTTPException(status_code=400, detail="A resposta do modelo não está no formato JSON esperado.")
        except Exception as e:
            # Tratar outros erros
            raise HTTPException(status_code=400, detail=str(e))
        
        # Registrar a consulta no QueryLog
        ip_address = request.client.host
        query_log = QueryLog(
            job_id=str(job_data.job_id),
            received_at=now,
            ip_address=ip_address,
            payload={
                "job_id": str(job_data.job_id),
                "attributes": job_data.attributes,
                "explanation": result + ": " + explanation
            }
        )
        db.add(query_log)
        db.commit()
        
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
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return JSONResponse(content={"message": "Tabelas recriadas com sucesso."}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recriar tabelas: {str(e)}")

# Configurar templates
templates = Jinja2Templates(directory="templates")

@app.get("/load-generator", response_class=HTMLResponse, tags=["Administração"])
async def load_generator_page(request: Request):
    """
    Renderiza a página para gerar cargas na aplicação.
    """
    return templates.TemplateResponse("load_generator.html", {"request": request})

class LoadGeneratorRequest(BaseModel):
    endpoint: str
    job_id: str
    history_days: int
    quantidade_linhas: int
    tamanho_arquivo: int
    min_value: int
    avg_value: int
    max_value: int
    stddev: int
    repeat: int
    delay: int
    variation_factor: float
    trend: str

@app.post("/generate-load", tags=["Administração"])
async def generate_load(request: LoadGeneratorRequest):
    """
    Gera cargas na aplicação com base nos parâmetros fornecidos.
    """

    print("Endpoint /generate-load chamado com os seguintes parâmetros:")
    print(f"endpoint: {request.endpoint}, job_id: {request.job_id}, history_days: {request.history_days}")
    print(f"quantidade_linhas: {request.quantidade_linhas}, tamanho_arquivo: {request.tamanho_arquivo}")
    print(f"min_value: {request.min_value}, avg_value: {request.avg_value}, max_value: {request.max_value}")
    print(f"stddev: {request.stddev}, repeat: {request.repeat}, delay: {request.delay}")
    print(f"variation_factor: {request.variation_factor}, trend: {request.trend}")

    base_payload = {
        "job_id": request.job_id,
        "monai_history_days": str(request.history_days),
        "attributes": {
            "quantidade_linhas": str(request.quantidade_linhas),
            "tamanho_arquivo": str(request.tamanho_arquivo),
            "min": str(request.min_value),
            "avg": str(request.avg_value),
            "max": str(request.max_value),
            "stddev": str(request.stddev),
        },
    }

    headers = {"Content-Type": "application/json"}

    def generate_payload(base_payload, variation_factor, trend=None, step=0.05):
        attributes = base_payload["attributes"]
        if trend == "up":
            scale_factor = 1 + step
        elif trend == "down":
            scale_factor = 1 - step
        else:
            scale_factor = 1 + random.uniform(-variation_factor, variation_factor)

        new_attributes = {}
        for key, value in attributes.items():
            if key in ["quantidade_linhas", "tamanho_arquivo", "min", "avg", "max", "stddev"]:
                base_value = int(value)
                new_value = int(base_value * scale_factor)
                if key == "max":
                    new_value = min(new_value, 999)
                else:
                    new_value = max(new_value, 0)
                new_attributes[key] = str(new_value)
            else:
                new_attributes[key] = value

        new_payload = base_payload.copy()
        new_payload["attributes"] = new_attributes
        return new_payload

    responses = []
    for _ in range(request.repeat):
        modified_payload = generate_payload(base_payload, request.variation_factor, request.trend)
        response = requests.post(request.endpoint, data=json.dumps(modified_payload), headers=headers)
        responses.append({"status_code": response.status_code, "response_text": response.text})
        time.sleep(request.delay)

    return {"message": "Cargas geradas com sucesso!!", "responses": responses}
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

# Verificar e criar tabelas no banco de dados
def create_tables():
    print("Verificando e criando tabelas no banco de dados, se necessário")
    Base.metadata.create_all(bind=engine)

# Inicializar a aplicação FastAPI
app = FastAPI()

# Chamar a função para verificar e criar tabelas
create_tables()

# Configurar timezone
def get_timezone():
    tz_name = os.getenv("TZ", "UTC")  # Padrão: UTC
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Timezone inválido: {tz_name}")

timezone = get_timezone()

# Função para obter o horário atual ajustado para o timezone configurado
def get_current_time():
    now_utc = datetime.utcnow()
    return now_utc.astimezone(timezone)

# Inicializar o cliente LLM com base nas variáveis de ambiente
def initialize_llm_client():
    llm_provider = os.getenv("MONAI_LLM", "OPENAI").upper()
    llm_model = os.getenv("MONAI_LLM_MODEL", "gpt-4")
    llm_key = os.getenv("MONAI_LLM_KEY")

    if not llm_key:
        raise ValueError("A variável de ambiente MONAI_LLM_KEY não está configurada.")

    if llm_provider == "OPENAI":
        from openai import OpenAI
        client = OpenAI(api_key=llm_key)
        return client, llm_model
    elif llm_provider == "GOOGLE":
        from google import genai
        client = genai.Client(api_key=llm_key)
        return client, llm_model
    elif llm_provider == "ANTHROPIC":
        from anthropic import Anthropic
        return Anthropic(api_key=llm_key), llm_model
    else:
        raise ValueError(f"Provedor de LLM desconhecido: {llm_provider}")

# Configuração do cliente LLM
client, llm_model = initialize_llm_client()

# Configuração de variáveis de ambiente
HISTORY_DAYS = int(os.getenv("MONAI_HISTORY_DAYS", 30))  # Padrão: 30 dias
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


@app.post("/jobs/", response_model=Union[JobDataResponse, dict])
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
            "Considere variações contextuais, padrões esperados e maior relevância nos dados históricos mais recentes.",
            f"Avaliando apenas este conjunto de dados {job_data.attributes}, caso sejam recebidos valores de 'min' e 'max', o valor de 'min' deve ser menor ou igual ao valor de 'max'.",
            f"Avaliando apenas este conjunto de dados {job_data.attributes}, caso sejam recebidos valores de 'avg' ou 'mean', 'min' e 'max', o valor de 'mean' ou 'avg' deve estar dentro do intervalo definido pelos valores de 'min' e 'max'.",
            f"Avaliando apenas este conjunto de dados {job_data.attributes}, caso sejam recebidos valores de 'stddev', 'min' e 'max', o valor de 'stddev' deve ser menor que a diferença entre 'max' e 'min'."
        ]

        # Adicionar regras adicionais para cada cenários de dados

        mandatory_rules = "".join([f"{i + 1}. {rule}\n" for i, rule in enumerate(rules)])

        prompt = (
            "Utilize técnicas de Análise Exploratória de Dados para entender as propriedades estatísticas e os padrões de cada um dos valores do conjunto de dados histórico abaixo e comparar com o último dado recebido."
            "As regras abaixo são obrigatórias para a análise e resultado:\n"
            f"{mandatory_rules}\n"
            "\n"
            f"Histórico de dados (últimas {history_days} entradas):\n{historical_attributes}\n\n"
            f"Novo dado recebido: \n{job_data.attributes}\nRecebido em {now}\nDia da semana: {weekday}\nFeriado: {is_holiday}\n\n"
            "Com base na análise, responda de forma objetiva, resumida e direta com uma das seguintes opções:\n"
            "'true': Se o novo dado segue o mesmo padrão do histórico fornecido.\n"
            "'false': Se o novo dado apresenta um padrão incomum dentro do histórico.\n"
            "Como saída a resposta deveobrigatóriamente deve ser formatada em um JSON contendo uma chave com o resultado da análise (true/false) e uma chave contendo a explicação resumida, caso a decisão tenha sido devido à uma regra obrigatória indicar qual delas. Exemplo:\n"
            "{\n"
            "  \"result\": \"false\",\n" 
            "  \"explain\": \"O novo dado apresenta uma anomalia significativa em seu valor de 'max', que é consideravelmente mais alto que os valores históricos...\"\n"
            "}\n"
            "Não incluir mais nenhuma informação ou caracter na repsosta além deste conteúdo de JSON, dado que a repsosta será importada como um JSON puro em outro sistema."
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
                temperature=0.1
            )
        elif os.getenv("MONAI_LLM", "OPENAI").upper() == 'GOOGLE':
            from google.genai import types
            response = client.models.generate_content(
                model=llm_model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction="Você é um analista de qualidade de dados altamente especializado.",
                    max_output_tokens=MAX_TOKENS,
                    temperature=0.1
                )
            )
        elif os.getenv("MONAI_LLM", "OPENAI").upper() == 'ANTHROPIC':
            response = client.messages.create(
                model=llm_model,
                system="Você é um analista de qualidade de dados altamente especializado. Sua tarefa é avaliar minuciosamente se os dados fornecidos seguem o mesmo padrão ou se há alguma anomalia.",
                max_tokens=MAX_TOKENS,
                temperature=0.1,
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
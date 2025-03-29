import os
from fastapi import HTTPException

def initialize_llm_client():
    """
    Inicializa o cliente LLM com base nas variáveis de ambiente.
    """
    llm_provider = os.getenv("MONAI_LLM", "OPENAI").upper()
    llm_model = os.getenv("MONAI_LLM_MODEL", "gpt-4")
    llm_key = os.getenv("MONAI_LLM_KEY")

    if not llm_key:
        raise ValueError("A variável de ambiente MONAI_LLM_KEY não está configurada.")

    if llm_provider == "OPENAI":
        from openai import OpenAI
        client = OpenAI(api_key=llm_key)
    elif llm_provider == "GOOGLE":
        from google import genai
        client = genai.Client(api_key=llm_key)
    elif llm_provider == "ANTHROPIC":
        from anthropic import Anthropic
        client = Anthropic(api_key=llm_key)
    else:
        raise ValueError(f"Provedor de LLM desconhecido: {llm_provider}")

    return client, llm_model, llm_provider

def send_prompt_to_llm(client, llm_model, llm_provider, prompt, max_tokens=200):
    """
    Envia o prompt ao LLM e retorna a resposta.
    """
    try:
        if llm_provider == "OPENAI":
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": "Você é um analista de qualidade de dados altamente especializado."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0
            )
            return response.choices[0].message.content.strip()
        elif llm_provider == "GOOGLE":
            from google.genai import types
            response = client.models.generate_content(
                model=llm_model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction="Você é um analista de qualidade de dados altamente especializado.",
                    temperature=0
                )
            )
            return getattr(response, "text", "").strip()
        elif llm_provider == "ANTHROPIC":
            response = client.messages.create(
                model=llm_model,
                system="Você é um analista de qualidade de dados altamente especializado.",
                max_tokens=max_tokens,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return getattr(response.content[0], "text", "").strip()
        else:
            raise ValueError("Cliente LLM não suportado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao interagir com o LLM: {str(e)}")
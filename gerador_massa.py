import requests
import time
import random
from datetime import datetime, timedelta
import json

# Configuração da API
API_URL = "http://localhost:8000"  # Ajuste conforme necessário

# Payload base com os novos campos
BASE_PAYLOAD = {
    "job_name": "processamento_diario",
    "job_filename": "arquivo_diario.csv",
    "attributes": {
        "quantidade_linhas": 1000,
        "tamanho_arquivo": 50000,
        "min": 10,
        "avg": 15,
        "max": 20,
        "stddev": 2.5
    },
    "use_historical_outlier": True,
    "force_true": False,
    "monai_history_executions": 30
}

def generate_payload(variation_factor=0.1, trend=None):
    """
    Gera um payload com variações nos valores base.
    
    Args:
        variation_factor (float): Fator de variação (0.0 a 1.0)
        trend (str, optional): Tendência para os valores ('up' ou 'down')
    """
    payload = BASE_PAYLOAD.copy()
    
    # Aplicar tendência se especificada
    if trend == 'up':
        base_multiplier = 1 + variation_factor
    elif trend == 'down':
        base_multiplier = 1 - variation_factor
    else:
        base_multiplier = 1
    
    # Gerar variações para cada atributo
    for key in payload["attributes"]:
        if isinstance(payload["attributes"][key], (int, float)):
            variation = random.uniform(-variation_factor, variation_factor)
            payload["attributes"][key] = int(payload["attributes"][key] * (base_multiplier + variation))
    
    return payload

def call_api(num_requests=10, delay=1, variation_factor=0.1, trend=None):
    """
    Faz chamadas para a API com payloads variados.
    
    Args:
        num_requests (int): Número de requisições a fazer
        delay (float): Delay entre as requisições em segundos
        variation_factor (float): Fator de variação para os valores
        trend (str, optional): Tendência para os valores ('up' ou 'down')
    """
    print(f"Iniciando {num_requests} chamadas para a API...")
    
    for i in range(num_requests):
        try:
            # Gerar payload com variações
            payload = generate_payload(variation_factor, trend)
            
            # Fazer a requisição
            response = requests.post(f"{API_URL}/jobs/", json=payload)
            
            # Verificar status da resposta
            if response.status_code == 200:
                print(f"Requisição {i+1}/{num_requests} - Sucesso")
                print(f"Payload: {json.dumps(payload, indent=2)}")
                print(f"Resposta: {response.json()}\n")
            else:
                print(f"Requisição {i+1}/{num_requests} - Erro: {response.status_code}")
                print(f"Payload: {json.dumps(payload, indent=2)}")
                print(f"Resposta: {response.text}\n")
            
            # Aguardar antes da próxima requisição
            time.sleep(delay)
            
        except Exception as e:
            print(f"Erro na requisição {i+1}: {str(e)}\n")
            time.sleep(delay)

if __name__ == "__main__":
    # Exemplo de uso
    print("Iniciando gerador de massa...")
    
    # Fazer chamadas com diferentes configurações
    print("\nFazendo chamadas com variação normal...")
    call_api(num_requests=5, delay=2, variation_factor=0.1)
    
    print("\nFazendo chamadas com tendência de aumento...")
    call_api(num_requests=5, delay=2, variation_factor=0.1, trend='up')
    
    print("\nFazendo chamadas com tendência de diminuição...")
    call_api(num_requests=5, delay=2, variation_factor=0.1, trend='down')
    
    print("\nGerador de massa concluído!")

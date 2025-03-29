import requests
import json
import time
import random

def generate_payload(base_payload, variation_factor, trend=None):
    """
    Gera um payload com variações proporcionais nos atributos.

    Args:
        base_payload (dict): Payload base para gerar variações.
        variation_factor (float): Fator de variação proporcional.
        trend (str): Tendência de variação ("up" para alta, "down" para baixa, None para aleatório).

    Returns:
        dict: Novo payload com atributos modificados.
    """
    attributes = base_payload["attributes"]
    new_attributes = {}

    for key, value in attributes.items():
        if key in ["quantidade_linhas", "tamanho_arquivo", "min", "avg", "max", "stddev"]:
            base_value = int(value)

            # Determinar o fator de escala com base na tendência
            if trend == "up":
                scale_factor = 1 + random.uniform(0, variation_factor)
            elif trend == "down":
                scale_factor = 1 - random.uniform(0, variation_factor)
            else:
                scale_factor = 1 + random.uniform(-variation_factor, variation_factor)

            # Calcular o novo valor
            new_value = int(base_value * scale_factor)

            # Restrições específicas para certos atributos
            if key == "max":
                new_value = min(new_value, 999)
            else:
                new_value = max(new_value, 0)

            new_attributes[key] = new_value  # Removido str()
        else:
            new_attributes[key] = value

    new_payload = base_payload.copy()
    new_payload["attributes"] = new_attributes
    return new_payload

def call_api(endpoint, payload, headers=None, repeat=10, delay=2, variation_factor=0.1, trend=None):
    """
    Envia requisições POST para a API com payloads gerados dinamicamente.

    Args:
        endpoint (str): URL do endpoint da API.
        payload (dict): Payload base para gerar variações.
        headers (dict): Cabeçalhos HTTP para a requisição.
        repeat (int): Número de requisições a serem enviadas.
        delay (int): Tempo de espera entre as requisições (em segundos).
        variation_factor (float): Fator de variação proporcional.
        trend (str): Tendência de variação ("up" para alta, "down" para baixa, None para aleatório).
    """
    for i in range(repeat):
        print(f"Gerando payload para a requisição {i + 1}/{repeat}...")
        modified_payload = generate_payload(payload, variation_factor, trend)
        print(f"Payload gerado: {modified_payload}")

        try:
            print(f"Enviando requisição {i + 1}/{repeat} para {endpoint}...")
            response = requests.post(endpoint, data=json.dumps(modified_payload), headers=headers, timeout=300)
            print(f"Request {i + 1}/{repeat} - Response: {response.status_code}, {response.text}")
        except requests.exceptions.Timeout:
            print(f"Timeout na requisição {i + 1}/{repeat}.")
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição {i + 1}/{repeat}: {e}")

        time.sleep(delay)

if __name__ == "__main__":
    API_ENDPOINT = "http://10.20.0.21:8009/jobs/"  # Substituir pela URL real
    HEADERS = {"Content-Type": "application/json"}
    
    BASE_PAYLOAD = {
        "job_id": "123e4567-e89b-12d3-a456-426614174001",
        "monai_history_executions": "30",
        "attributes": {
            "quantidade_linhas": "100000",
            "tamanho_arquivo": "1000",
            "min": "300",
            "avg": "550",
            "max": "999",
            "stddev": "200"
        }
    }
    
    # Configuração para geração de massa
    call_api(
        API_ENDPOINT,
        BASE_PAYLOAD,
        headers=HEADERS,
        repeat=5,  # Reduzido para 5 requisições para teste
        delay=1,
        variation_factor=0.1,
        trend="up"  # Alterar para "down" ou None conforme necessário
    )

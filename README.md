# MonAI - Sistema de Análise de Dados com LLMs

Este projeto é uma API construída com **FastAPI** para análise de dados utilizando modelos de linguagem (LLMs) como **OpenAI**, **Google Gemini** e **Anthropic Sonnet**. A aplicação permite o envio de dados para avaliação, comparando-os com históricos armazenados em um banco de dados PostgreSQL.

## Funcionalidades

- Suporte a múltiplos provedores de LLMs:
  - **OpenAI** (ex.: GPT-4)
  - **Google Gemini**
  - **Anthropic Sonnet**
- Registro de dados recebidos e históricos no banco de dados.
- Avaliação de consistência dos dados com base em padrões históricos.
- Identificação de anomalias nos dados recebidos.
- Suporte a feriados e dias da semana para análise contextual.
- Configuração de timezone com base na variável de ambiente `TZ`.
- Sistema de regras flexível com grupos de regras.
- Validações matemáticas e estatísticas automatizadas.

## Estrutura do Projeto

```bash
.
├── main.py                # Arquivo principal da aplicação
├── database.py            # Configuração do banco de dados
├── models.py              # Modelos do SQLAlchemy
├── schemas.py             # Esquemas do Pydantic para validação de dados
├── llm_client.py          # Cliente para interação com provedores de LLMs
├── requirements.txt       # Dependências do projeto
├── Dockerfile            # Configuração para container Docker
├── start.sh              # Script de inicialização do container
├── populate_initial_data.py # Script para popular dados iniciais
├── gerador_massa.py      # Script para geração de massa de dados
├── .env.example          # Exemplo de configuração de variáveis de ambiente
├── .gitignore            # Arquivos ignorados pelo Git
└── .gitea/workflows/     # Configuração de CI/CD
```

### Descrição dos Arquivos

- **`main.py`**: Contém a lógica principal da aplicação e os endpoints da API.
- **`database.py`**: Configuração do banco de dados e inicialização do SQLAlchemy.
- **`models.py`**: Define os modelos do banco de dados usando SQLAlchemy.
- **`schemas.py`**: Define os esquemas de validação de dados usando Pydantic.
- **`llm_client.py`**: Implementa a lógica para inicializar e interagir com provedores de LLMs.
- **`start.sh`**: Script de inicialização que executa a população de dados e inicia a aplicação.
- **`populate_initial_data.py`**: Script para popular o banco com dados iniciais e regras padrão.
- **`gerador_massa.py`**: Script para geração de massa de dados e envio para a API.

## Estrutura do Banco de Dados

### Tabela `job_data`

| Campo                  | Tipo       | Descrição                                      |
|------------------------|------------|-----------------------------------------------|
| `id`                   | UUID       | Identificador único do registro.              |
| `job_id`               | UUID       | Identificador do job associado.               |
| `attributes`           | JSON       | Atributos do job.                             |
| `received_at`          | DateTime   | Data e hora de recebimento do registro.       |
| `weekday`              | String     | Dia da semana em que o registro foi recebido. |
| `month`                | String     | Mês em que o registro foi recebido.           |
| `is_holiday`           | Boolean    | Indica se o dia é feriado.                    |
| `outlier_data`         | Boolean    | Indica se o registro é considerado um outlier.|
| `force_true`           | Boolean    | Indica se o resultado foi forçado como verdadeiro.|

### Tabela `query_log`

| Campo                  | Tipo       | Descrição                                      |
|------------------------|------------|-----------------------------------------------|
| `id`                   | UUID       | Identificador único do registro.              |
| `job_id`               | UUID       | Identificador do job associado.               |
| `attributes`           | JSON       | Atributos do job.                             |
| `result`               | String     | Resultado da análise (`true` ou `false`).     |
| `explanation`          | Text       | Explicação do resultado da análise.           |
| `referer`              | String     | Referência da requisição.                     |
| `fingerprint`          | String     | Identificador único da requisição.            |
| `received_at`          | DateTime   | Data e hora de recebimento do registro.       |
| `ip_address`           | String     | Endereço IP do cliente.                       |
| `user_agent`           | String     | User-Agent do cliente.                        |
| `monai_history_executions` | Integer | Número de execuções históricas consideradas.  |
| `force_true`           | Boolean    | Indica se o resultado foi forçado como verdadeiro.|
| `use_historical_outlier` | Boolean  | Indica se outliers históricos foram utilizados.|

### Tabela `job`

| Campo                  | Tipo       | Descrição                                      |
|------------------------|------------|-----------------------------------------------|
| `id`                   | String     | Identificador único do job (SHA-256).         |
| `job_name`             | String     | Nome do job.                                   |
| `job_filename`         | String     | Nome do arquivo do job.                        |
| `description`          | String     | Descrição do job.                              |
| `is_active`            | Boolean    | Indica se o job está ativo.                    |
| `rule_groups`          | List       | Grupos de regras associados ao job.            |

### Tabela `rule`

| Campo                  | Tipo       | Descrição                                      |
|------------------------|------------|-----------------------------------------------|
| `id`                   | UUID       | Identificador único da regra.                  |
| `name`                 | String     | Nome da regra.                                 |
| `description`          | String     | Descrição da regra.                            |
| `rule_text`            | String     | Texto da regra para validação.                 |
| `is_active`            | Boolean    | Indica se a regra está ativa.                  |

### Tabela `rule_group`

| Campo                  | Tipo       | Descrição                                      |
|------------------------|------------|-----------------------------------------------|
| `id`                   | UUID       | Identificador único do grupo.                  |
| `name`                 | String     | Nome do grupo de regras.                       |
| `description`          | String     | Descrição do grupo.                            |
| `is_active`            | Boolean    | Indica se o grupo está ativo.                  |
| `rules`                | List       | Regras associadas ao grupo.                    |

## Pré-requisitos

- **Python 3.10+**
- **PostgreSQL**
- **Chaves de API** para os provedores de LLMs (OpenAI, Google Gemini ou Anthropic Sonnet).

## Instalação

1. Clone o repositório:
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd monai
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente: Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
   ```bash
   MONAI_DATABASE_URL=postgresql://<usuario>:<senha>@<host>:<porta>/<nome_do_banco>
   MONAI_LLM=OPENAI  # Opções: OPENAI, GOOGLE, ANTHROPIC
   MONAI_LLM_MODEL=gpt-4
   MONAI_LLM_KEY=<sua_chave_de_api>
   TZ=America/Sao_Paulo  # Opcional: Configuração de timezone
   MONAI_HISTORY_EXECUTIONS=30  # Número de execuções de histórico (padrão: 30)
   ```

## Variáveis de Ambiente

| Variável                  | Descrição                                                                 | Exemplo                          |
|---------------------------|---------------------------------------------------------------------------|----------------------------------|
| `MONAI_DATABASE_URL`      | URL de conexão com o banco de dados PostgreSQL.                          | `postgresql://user:pass@host:5432/dbname` |
| `MONAI_LLM`               | Provedor de LLM a ser utilizado.                                         | `OPENAI`, `GOOGLE`, `ANTHROPIC` |
| `MONAI_LLM_MODEL`         | Modelo do LLM a ser utilizado.                                           | `gpt-4`, `gemini`, `claude`     |
| `MONAI_LLM_KEY`           | Chave de API para o provedor de LLM.                                     | `sk-1234567890abcdef`           |
| `TZ`                      | Timezone para ajustar os horários.                                       | `America/Sao_Paulo`             |
| `MONAI_HISTORY_EXECUTIONS`| Número de execuções de histórico para análise.                           | `30`                            |
| `MONAI_MAX_TOKENS`        | Limite máximo de tokens para respostas LLM.                              | `200`                           |

## Uso

1. Execute a aplicação:
   ```bash
   uvicorn main:app --reload
   ```

2. Acesse a documentação interativa da API:
   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

3. Envie uma requisição para o endpoint `/jobs/data/`:
   - **Exemplo de requisição:**
     ```bash
     POST /jobs/data/
     Content-Type: application/json
     ```
     
     ```json
     {
       "job_name": "Envio Diário Base Full - Banco Joelma",
       "job_filename": "BASEDIARIA.csv",
       "monai_history_executions": 7,
       "attributes": {
         "quantidade_linhas": "80000",
         "tamanho_arquivo": "800",
         "score001_min": "106",
         "score001_avg": "450",
         "score001_max": "1074",
         "score001_stddev": "218",
         "score002_min": "50",
         "score002_avg": "100",
         "score002_max": "107",
         "score002_stddev": "28"
       }
     }
     ```

## Docker

1. Construa a imagem Docker:
   ```bash
   docker build -t monai .
   ```

2. Execute o contêiner:
   ```bash
   docker run -d -p 8000:8000 --env-file .env monai
   ```

## Dependências

As dependências do projeto estão listadas no arquivo [`requirements.txt`](requirements.txt). Abaixo estão as principais bibliotecas utilizadas:

- **FastAPI**: Framework web para construir APIs.
- **Uvicorn**: Servidor ASGI para rodar a aplicação FastAPI.
- **SQLAlchemy**: ORM para interagir com o banco de dados.
- **Psycopg2-binary**: Driver PostgreSQL para Python.
- **Pydantic**: Validação de dados e esquemas.
- **Holidays**: Biblioteca para cálculo de feriados.
- **OpenAI**: Cliente para interagir com a API OpenAI.
- **Google Generative AI**: Cliente para interagir com a API Gemini (Google).
- **Anthropic**: Cliente para interagir com a API Anthropic (Sonnet).
- **Python-dotenv**: Para carregar variáveis de ambiente de arquivos `.env`.
- **Httpx**: Cliente HTTP para interagir com APIs.

## Endpoints da API

### POST /jobs/data/
Endpoint para envio de dados para análise.

**Parâmetros:**
```json
{
  "job_name": "string",
  "job_filename": "string",
  "monai_history_executions": "int",
  "attributes": {
    "campo1": "valor1",
    "campo2": "valor2"
  },
  "use_historical_outlier": "boolean (opcional)",
  "force_true": "boolean (opcional)"
}
```

### POST /rules/
Endpoint para criar uma nova regra.

**Parâmetros:**
```json
{
  "name": "string",
  "description": "string",
  "rule_text": "string",
  "is_active": "boolean"
}
```

### POST /rule-groups/
Endpoint para criar um novo grupo de regras.

**Parâmetros:**
```json
{
  "name": "string",
  "description": "string",
  "is_active": "boolean",
  "rule_ids": ["uuid"]
}
```

### POST /jobs/create/
Endpoint para criar um novo job.

**Parâmetros:**
```json
{
  "job_name": "string",
  "job_filename": "string",
  "description": "string",
  "is_active": "boolean",
  "rule_group_ids": ["uuid"]
}
```

## Configurações Avançadas

### Variáveis de Ambiente Adicionais
| Variável           | Descrição                                  | Exemplo        |
|-------------------|---------------------------------------------|----------------|
| `MONAI_MAX_TOKENS`| Limite máximo de tokens para respostas LLM | `200`         |

### Modelos LLM Suportados
- **OpenAI**: gpt-4, gpt-3.5-turbo
- **Google**: gemini-pro
- **Anthropic**: claude-3-sonnet

## Tratamento de Erros

A API utiliza os seguintes códigos de erro HTTP:

### 400 Bad Request
- Quando o número de histórico de execuções é menor ou igual a zero
- Quando os dados enviados não atendem aos critérios de validação
- Quando o resultado da análise é "false"
- Quando ocorre qualquer erro de validação dos dados

### 500 Internal Server Error
- Erros ao interagir com o LLM (OpenAI, Google Gemini, Anthropic)
- Erros ao recriar tabelas no banco de dados

### Mensagens de Erro Específicas
- `"A variável de ambiente MONAI_LLM_KEY não está configurada."`
- `"Provedor de LLM desconhecido: {provider}"`
- `"A resposta do modelo não contém as chaves esperadas: 'result' e 'explain'."`
- `"O valor de 'result' na resposta do modelo é inválido."`
- `"É necessário pelo menos {x} execuções de dados históricos para avaliação, mas apenas {y} estão disponíveis."`

## Segurança

### Práticas Implementadas
1. **Variáveis de Ambiente**
   - Todas as chaves de API e configurações sensíveis são gerenciadas via variáveis de ambiente
   - Arquivo `.env` incluído no `.gitignore` para evitar exposição de credenciais

2. **Fingerprint de Requisições**
   - Cada requisição é identificada por um fingerprint único baseado em:
     - IP do cliente
     - User-Agent
     - Referer

3. **Validação de Dados**
   - Validação rigorosa de todos os dados de entrada usando Pydantic
   - Tipagem forte para todos os campos
   - Validações customizadas para campos específicos

4. **Logs de Acesso**
   - Registro detalhado de todas as requisições no `QueryLog`
   - Armazenamento de informações de origem (IP, User-Agent, Referer)

### Recomendações
1. Implementar autenticação e autorização (JWT, OAuth2)
2. Configurar rate limiting para prevenir abusos
3. Utilizar HTTPS em produção
4. Manter as dependências atualizadas
5. Realizar backups regulares do banco de dados

## Monitoramento e Logs

### Logs da Aplicação
1. **Logs de Requisições**
   - Todas as requisições são registradas na tabela `query_log`
   - Informações armazenadas:
     - ID do job
     - Atributos
     - Resultado
     - Explicação
     - IP do cliente
     - User-Agent
     - Referer
     - Timestamp
     - Número de execuções históricas

2. **Logs de Dados**
   - Registros armazenados na tabela `job_data`
   - Informações incluem:
     - Dados do job
     - Timestamp
     - Contexto temporal (dia da semana, mês, feriado)
     - Status de outlier

### Monitoramento
1. **Métricas Importantes**
   - Taxa de sucesso/falha das análises
   - Tempo de resposta do LLM
   - Uso de recursos do banco de dados
   - Número de requisições por período

2. **Alertas Recomendados**
   - Erros de conexão com LLM
   - Falhas no banco de dados
   - Alta taxa de outliers
   - Tempo de resposta elevado

## Testes

### Tipos de Testes
1. **Testes Unitários**
   - Validação de modelos Pydantic
   - Funções de utilidade
   - Regras de análise

2. **Testes de Integração**
   - Conexão com banco de dados
   - Integração com LLMs
   - Endpoints da API

3. **Testes de Carga**
   - Utilizando o script `gerador_massa.py`
   - Simulação de diferentes cenários
   - Verificação de performance

### Executando os Testes
```bash
# Testes unitários
pytest tests/unit

# Testes de integração
pytest tests/integration

# Testes de carga
python gerador_massa.py
```

## CI/CD

O pipeline de CI/CD é configurado usando Gitea Actions (`.gitea/workflows/build.yaml`):

### Etapas do Pipeline
1. **Checkout do Código**
   - Clonagem do repositório

2. **Build da Imagem Docker**
   - Construção da imagem usando Dockerfile
   - Suporte para múltiplas arquiteturas (amd64, arm64)

3. **Push para Registry**
   - Upload da imagem para o registry do Gitea
   - Tagging automático

### Configurações Necessárias
- `GIT_REGISTRY_USER`: Usuário do registry
- `GIT_REGISTRY_PASSWORD`: Senha do registry
- `GIT_REGISTRY`: URL do registry
- `GIT_OWNER`: Proprietário do repositório

## Regras de Análise

A API implementa diversas regras para análise de dados estatísticos:

### Regras Mandatórias
1. **Validação de Médias**
   - `avg` e `mean` devem estar entre `min` e `max`

2. **Validação de Limites**
   - `max` deve ser maior que `min`
   - `median` deve estar entre `min` e `max`
   - `mode` deve estar entre `min` e `max`

3. **Validação de Medidas de Dispersão**
   - `std` e `stdev` devem ser menores que `(max - min)`
   - `variance`, `skewness`, `kurtosis` devem ser positivos

4. **Validação de Contagens**
   - `count` deve ser maior que zero
   - `sum` deve ser maior que zero

### Contexto Temporal
- Consideração de dia da semana
- Consideração de mês
- Identificação de feriados

## Gerador de Massa

O script `gerador_massa.py` permite gerar dados de teste:

### Configurações
```python
BASE_PAYLOAD = {
    "job_name": "Envio Diário Base Full - Banco Joelma",
    "job_filename": "BASEDIARIA.csv",
    "monai_history_executions": "20",
    "attributes": {
        "quantidade_linhas": "70000",
        "tamanho_arquivo": "700",
        "min": "100",
        "avg": "350",
        "max": "499",
        "stddev": "200"
    }
}
```

### Parâmetros
- `repeat`: Número de requisições (default: 30)
- `delay`: Intervalo entre requisições (default: 1s)
- `variation_factor`: Fator de variação (default: 0.1)
- `trend`: Tendência dos dados ("up", "down", None)

### Uso
```bash
python gerador_massa.py
```

## Gerenciamento do Banco de Dados

### Tabelas Principais
1. **job_data**
   - Armazena dados históricos dos jobs
   - Inclui metadados temporais
   - Rastreia outliers

2. **query_log**
   - Registra todas as consultas
   - Armazena resultados e explicações
   - Mantém dados de auditoria

3. **job**
   - Armazena informações dos jobs
   - Gerencia associações com grupos de regras

4. **rule**
   - Armazena regras de validação
   - Gerencia regras ativas/inativas

5. **rule_group**
   - Agrupa regras relacionadas
   - Gerencia grupos ativos/inativos

### Manutenção
1. **Recriação de Tabelas**
   ```bash
   POST /recreate-tables/
   ```

2. **Backup**
   ```bash
   pg_dump -U <usuario> -d <banco> > backup.sql
   ```

3. **Restore**
   ```bash
   psql -U <usuario> -d <banco> < backup.sql
   ```

4. **Limpeza de Dados**
   - Implementar política de retenção
   - Arquivar dados antigos
   - Manter índices otimizados

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE). Você é livre para usar, modificar e distribuir este software, desde que mantenha a atribuição original e inclua uma cópia da licença.
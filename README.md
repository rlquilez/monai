# MonAI - Sistema de Análise de Dados com LLMs

Este projeto é uma API construída com **FastAPI** para análise de dados utilizando modelos de linguagem (LLMs) como **OpenAI**, **Google Gemini** e **Anthropic Sonnet**. A aplicação permite o envio de dados para avaliação, comparando-os com históricos armazenados em um banco de dados PostgreSQL.

---

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

---

## Estrutura do Projeto

```bash
.
├── main.py            # Arquivo principal da aplicação
├── database.py        # Configuração do banco de dados
├── models.py          # Modelos do SQLAlchemy
├── schemas.py         # Esquemas do Pydantic
├── requirements.txt   # Dependências do projeto
├── Dockerfile         # Configuração para container Docker
├── .gitignore         # Arquivos ignorados pelo Git
└── .gitea/workflows/  # Configuração de CI/CD
```

---

## Pré-requisitos

- **Python 3.10+**
- **PostgreSQL**
- **Chaves de API** para os provedores de LLMs (OpenAI, Google Gemini ou Anthropic Sonnet).

---

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
   MONAI_HISTORY_DAYS=30  # Opcional: Número de dias de histórico (padrão: 30 dias)
   ```

---

## Variáveis de Ambiente

| Variável            | Descrição                                                                 | Exemplo                          |
|---------------------|---------------------------------------------------------------------------|----------------------------------|
| `MONAI_DATABASE_URL`| URL de conexão com o banco de dados PostgreSQL.                          | `postgresql://user:pass@host:5432/dbname` |
| `MONAI_LLM`         | Provedor de LLM a ser utilizado.                                         | `OPENAI`, `GOOGLE`, `ANTHROPIC` |
| `MONAI_LLM_MODEL`   | Modelo do LLM a ser utilizado.                                           | `gpt-4`, `gemini`, `claude`     |
| `MONAI_LLM_KEY`     | Chave de API para o provedor de LLM.                                     | `sk-1234567890abcdef`           |
| `TZ`                | Timezone para ajustar os horários.                                       | `America/Sao_Paulo`             |
| `MONAI_HISTORY_DAYS`| Número de dias de histórico para análise.                                | `30`                            |

---

## Uso

1. Execute a aplicação:
   ```bash
   uvicorn main:app --reload
   ```

2. Acesse a documentação interativa da API:
   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

3. Envie uma requisição para o endpoint `/jobs/`:
   - **Exemplo de requisição:**
     ```bash
     POST /jobs/
     Content-Type: application/json
     ```
     
     ```json
     {
       "job_id": "123e4567-e89b-12d3-a456-426614174000",
       "monai_history_days": 7,
       "attributes": {
         "média": 50,
         "máximo": 60
       }
     }
     ```

---

## Docker

1. Construa a imagem Docker:
   ```bash
   docker build -t monai .
   ```

2. Execute o contêiner:
   ```bash
   docker run -d -p 8000:8000 --env-file .env monai
   ```

---

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

---

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE). Você é livre para usar, modificar e distribuir este software, desde que mantenha a atribuição original e inclua uma cópia da licença.
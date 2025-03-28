# Use uma imagem base do Python
FROM python:3.13-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de dependências
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Executa o script para criar o usuário padrão
RUN python create_user.py

# Expõe as portas para a API e o console
EXPOSE 8000
EXPOSE 8001

# Comando para iniciar os dois servidores
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 & uvicorn console:console_app --host 0.0.0.0 --port 8001"]
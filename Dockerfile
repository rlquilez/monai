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

# Expõe a porta que o FastAPI usará
EXPOSE 8000

# Script de inicialização
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Comando para iniciar a aplicação
CMD ["/start.sh"]
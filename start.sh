#!/bin/bash

# Executa o script de população de dados
echo "Verificando e populando dados iniciais..."
python populate_initial_data.py

# Inicia a aplicação FastAPI
echo "Iniciando a aplicação FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 
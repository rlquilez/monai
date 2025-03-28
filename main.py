import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base
from routers import auth, jobs, rules, dashboard

# Verificar e criar tabelas no banco de dados
def create_tables():
    print("Verificando e criando tabelas no banco de dados, se necessário")
    Base.metadata.create_all(bind=engine)

# Inicializar a aplicação FastAPI para a API
app = FastAPI(title="MonAI API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chamar a função para verificar e criar tabelas
create_tables()

# Configurar rotas da API
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(rules.router, prefix="/rules", tags=["rules"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
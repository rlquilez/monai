import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import admin

# Inicializar a aplicação FastAPI para o console administrativo
console_app = FastAPI(title="MonAI Console")

# Configurar CORS
console_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos e templates
console_app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configurar rotas do console administrativo
console_app.include_router(admin.router, prefix="/console", tags=["admin"])
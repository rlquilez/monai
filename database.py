import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Obtém a URL do banco de dados a partir da variável de ambiente
DATABASE_URL = os.getenv("MONAI_DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não está configurada.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
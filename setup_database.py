import os
from alembic.config import Config
from alembic import command
from populate_rules import populate_rules

def setup_database():
    """
    Executa as migrações do banco de dados e popula as regras padrão.
    """
    # Configurar o Alembic
    alembic_cfg = Config("alembic.ini")
    
    # Executar as migrações
    print("Executando migrações do banco de dados...")
    command.upgrade(alembic_cfg, "head")
    
    # Popular as regras
    print("Populando regras padrão...")
    populate_rules()
    
    print("Configuração do banco de dados concluída!")

if __name__ == "__main__":
    setup_database() 
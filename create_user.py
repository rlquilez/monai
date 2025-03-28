from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(username: str, password: str, role: str = "admin"):
    db: Session = SessionLocal()
    try:
        # Verificar se o usuário já existe
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"Usuário '{username}' já existe. Nenhuma ação necessária.")
            return

        # Criar o usuário
        hashed_password = pwd_context.hash(password)
        user = User(username=username, hashed_password=hashed_password, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Usuário criado com sucesso: {user.username}")
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Substitua "admin" e "senha123" pelos valores desejados
    create_user(username="admin", password="senha123", role="admin")
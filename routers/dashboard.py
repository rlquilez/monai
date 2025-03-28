from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import QueryLog

router = APIRouter()

@router.get("/")
def get_dashboard_data(db: Session = Depends(get_db)):
    logs = db.query(QueryLog).all()
    return {"total_queries": len(logs)}

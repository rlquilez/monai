from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Rule
from schemas import RuleCreate, RuleResponse

router = APIRouter()

@router.post("/", response_model=RuleResponse)
def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    new_rule = Rule(**rule.dict())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@router.get("/", response_model=List[RuleResponse])
def list_rules(db: Session = Depends(get_db)):
    return db.query(Rule).all()

@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(rule_id: UUID, rule: RuleCreate, db: Session = Depends(get_db)):
    existing_rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not existing_rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    for key, value in rule.dict(exclude_unset=True).items():
        setattr(existing_rule, key, value)
    db.commit()
    return existing_rule

@router.delete("/{rule_id}")
def delete_rule(rule_id: UUID, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    db.delete(rule)
    db.commit()
    return {"message": "Regra excluída com sucesso"}
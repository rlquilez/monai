from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User, JobData, Rule, QueryLog
from schemas import UserCreate, JobDataCreate, RuleCreate
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Login route
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    username: str = Form(...),  # Accept the `username` field as form data
    password: str = Form(...),  # Accept the `password` field as form data
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/console/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

# Dashboard route
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    logs = db.query(QueryLog).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "logs": logs})

# Jobs management
@router.get("/jobs", response_class=HTMLResponse)
def manage_jobs(request: Request, db: Session = Depends(get_db)):
    jobs = db.query(JobData).all()
    return templates.TemplateResponse("manage_jobs.html", {"request": request, "jobs": jobs})

@router.post("/jobs")
def create_job(job: JobDataCreate, db: Session = Depends(get_db)):
    new_job = JobData(**job.dict())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return {"message": "Job created successfully", "job": new_job}

# Rules management
@router.get("/rules", response_class=HTMLResponse)
def manage_rules(request: Request, db: Session = Depends(get_db)):
    rules = db.query(Rule).all()
    return templates.TemplateResponse("manage_rules.html", {"request": request, "rules": rules})

@router.post("/rules")
def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    new_rule = Rule(**rule.dict())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return {"message": "Rule created successfully", "rule": new_rule}
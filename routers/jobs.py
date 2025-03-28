# filepath: /Users/rodrigo/Documents/PESSOAL/dev/monai/routers/jobs.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import JobData
from schemas import JobDataCreate, JobDataResponse

router = APIRouter()

@router.post("/", response_model=JobDataResponse)
def create_job(job: JobDataCreate, db: Session = Depends(get_db)):
    new_job = JobData(**job.dict())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

@router.get("/", response_model=List[JobDataResponse])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(JobData).all()

@router.put("/{job_id}", response_model=JobDataResponse)
def update_job(job_id: UUID, job: JobDataCreate, db: Session = Depends(get_db)):
    existing_job = db.query(JobData).filter(JobData.id == job_id).first()
    if not existing_job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    for key, value in job.dict(exclude_unset=True).items():
        setattr(existing_job, key, value)
    db.commit()
    return existing_job

@router.delete("/{job_id}")
def delete_job(job_id: UUID, db: Session = Depends(get_db)):
    job = db.query(JobData).filter(JobData.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    db.delete(job)
    db.commit()
    return {"message": "Job excluído com sucesso"}
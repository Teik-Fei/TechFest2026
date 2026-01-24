from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from database import engine, get_db
from ai_service import (
    extract_skills_from_job, 
    calculate_skill_match, 
    generate_upskilling_roadmap,
    extract_skills_from_resume
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TechFest Job Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== JOB ENDPOINTS =====

@app.get("/api/jobs", response_model=List[schemas.Job])
def get_jobs(
    skip: int = 0,
    limit: int = 50,
    employment_type: Optional[str] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all jobs with optional filters"""
    query = db.query(models.Job)
    
    if employment_type:
        query = query.filter(models.Job.employment_type.contains(employment_type))
    if location:
        query = query.filter(models.Job.location.contains(location))
    if company:
        query = query.filter(models.Job.company.contains(company))
    if search:
        query = query.filter(
            (models.Job.title.contains(search)) | 
            (models.Job.company.contains(search)) |
            (models.Job.job_description.contains(search))
        )
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@app.get("/api/jobs/{job_id}", response_model=schemas.Job)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get single job by ID"""
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/jobs/stats/summary")
def get_stats(db: Session = Depends(get_db)):
    """Get job statistics"""
    total_jobs = db.query(models.Job).count()
    companies = db.query(models.Job.company).distinct().count()
    employment_types = db.query(models.Job.employment_type).distinct().all()
    
    return {
        "total_jobs": total_jobs,
        "total_companies": companies,
        "employment_types": [e[0] for e in employment_types if e[0]]
    }

# ===== USER ENDPOINTS =====

@app.post("/api/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create new user profile"""
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/users/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ===== APPLICATION TRACKING =====

@app.post("/api/applications", response_model=schemas.Application)
def create_application(app: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    """Create new job application"""
    db_app = models.Application(**app.dict())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@app.get("/api/applications/user/{user_id}")
def get_user_applications(user_id: int, db: Session = Depends(get_db)):
    """Get all applications for a user"""
    apps = db.query(models.Application).filter(
        models.Application.user_id == user_id
    ).all()
    
    results = []
    for app in apps:
        job = db.query(models.Job).filter(models.Job.id == app.job_id).first()
        results.append({
            "id": app.id,
            "status": app.status,
            "applied_at": app.applied_at,
            "notes": app.notes,
            "job": {
                "id": job.id,
                "title": job.title,
                "company": job.company
            } if job else None
        })
    return results

@app.put("/api/applications/{app_id}/status")
def update_application_status(app_id: int, status: str, db: Session = Depends(get_db)):
    """Update application status"""
    app = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.status = status
    db.commit()
    return {"message": "Status updated", "status": status}

# ===== AI ENDPOINTS =====

@app.post("/api/ai/extract-job-skills/{job_id}")
def api_extract_job_skills(job_id: int, db: Session = Depends(get_db)):
    """Extract and save skills for a job using AI"""
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.required_skills and len(job.required_skills) > 0:
        return {"job_id": job_id, "skills": job.required_skills, "cached": True}
    
    skills = extract_skills_from_job(job.job_description or "")
    job.required_skills = skills
    db.commit()
    
    return {"job_id": job_id, "skills": skills, "cached": False}

@app.post("/api/ai/match-skills", response_model=schemas.SkillMatchResponse)
def api_match_skills(user_id: int, job_id: int, db: Session = Depends(get_db)):
    """Calculate skill match between user and job"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    
    if not user or not job:
        raise HTTPException(status_code=404, detail="User or Job not found")
    
    if not job.required_skills or len(job.required_skills) == 0:
        job.required_skills = extract_skills_from_job(job.job_description or "")
        db.commit()
    
    match_result = calculate_skill_match(user.skills or [], job.required_skills or [])
    
    return {
        "job_id": job.id,
        "job_title": job.title,
        **match_result
    }

@app.post("/api/ai/generate-roadmap")
def api_create_roadmap(user_id: int, job_id: int, db: Session = Depends(get_db)):
    """Generate personalized upskilling roadmap"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    
    if not user or not job:
        raise HTTPException(status_code=404, detail="User or Job not found")
    
    if not job.required_skills or len(job.required_skills) == 0:
        job.required_skills = extract_skills_from_job(job.job_description or "")
        db.commit()
    
    match_result = calculate_skill_match(user.skills or [], job.required_skills or [])
    roadmap = generate_upskilling_roadmap(
        user.skills or [],
        job.title,
        match_result["missing_skills"]
    )
    
    roadmap["job_title"] = job.title
    roadmap["job_company"] = job.company
    roadmap["match_percentage"] = match_result["match_percentage"]
    
    return roadmap

@app.post("/api/ai/parse-resume")
def api_parse_resume(resume_text: str, db: Session = Depends(get_db)):
    """Extract skills from resume text"""
    skills = extract_skills_from_resume(resume_text)
    return {"extracted_skills": skills, "count": len(skills)}

@app.post("/api/ai/bulk-extract-skills")
def bulk_extract_skills(limit: int = 10, db: Session = Depends(get_db)):
    """Extract skills for jobs that don't have them yet"""
    jobs = db.query(models.Job).filter(
        (models.Job.required_skills == None) | (models.Job.required_skills == [])
    ).limit(limit).all()
    
    updated = 0
    for job in jobs:
        try:
            skills = extract_skills_from_job(job.job_description or "")
            job.required_skills = skills
            updated += 1
        except Exception as e:
            print(f"Error processing job {job.id}: {e}")
    
    db.commit()
    return {"message": f"Updated {updated} jobs", "processed": len(jobs)}

@app.get("/")
def root():
    return {
        "message": "TechFest Job Platform API",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
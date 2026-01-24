from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
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
from file_utils import (
    extract_text_from_file,
    extract_email_from_text,
    extract_name_from_filename
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Job Match Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== JOB ENDPOINTS =====

@app.get("/api/jobs")
def get_jobs(
    skip: int = 0,
    limit: int =349,
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
            (models.Job.location.contains(search))
        )
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@app.get("/api/jobs/{job_id}", response_model=schemas.Job)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a single job by ID"""
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/jobs/stats/overview")
def get_job_stats(db: Session = Depends(get_db)):
    """Get overview statistics about jobs"""
    total_jobs = db.query(models.Job).count()
    
    companies = db.query(models.Job.company).distinct().count()
    
    locations = db.query(models.Job.location).distinct().all()
    
    employment_types = db.query(models.Job.employment_type).distinct().all()
    
    return {
        "total_jobs": total_jobs,
        "total_companies": companies,
        "locations": [loc[0] for loc in locations if loc[0]],
        "employment_types": [e[0] for e in employment_types if e[0]]
    }

# ===== USER ENDPOINTS =====

@app.post("/api/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create new user profile or return existing user"""
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        return existing_user
    
    # Create new user
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

# ===== APPLICATION ENDPOINTS =====

@app.post("/api/applications", response_model=schemas.Application)
def create_application(application: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    """Create a job application"""
    user = db.query(models.User).filter(models.User.id == application.user_id).first()
    job = db.query(models.Job).filter(models.Job.id == application.job_id).first()
    
    if not user or not job:
        raise HTTPException(status_code=404, detail="User or Job not found")
    
    existing = db.query(models.Application).filter(
        models.Application.user_id == application.user_id,
        models.Application.job_id == application.job_id
    ).first()
    
    if existing:
        return existing
    
    db_application = models.Application(**application.dict())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

@app.get("/api/applications/user/{user_id}")
def get_user_applications(user_id: int, db: Session = Depends(get_db)):
    """Get all applications for a user"""
    applications = db.query(models.Application).filter(
        models.Application.user_id == user_id
    ).all()
    
    results = []
    for app in applications:
        job = db.query(models.Job).filter(models.Job.id == app.job_id).first()
        results.append({
            "id": app.id,
            "job_id": app.job_id,
            "job_title": job.title if job else "Unknown",
            "company": job.company if job else "Unknown",
            "status": app.status,
            "applied_at": app.applied_at
        })
    
    return results

# ===== AI ENDPOINTS =====

@app.post("/api/ai/extract-job-skills/{job_id}")
def api_extract_job_skills(job_id: int, db: Session = Depends(get_db)):
    """Extract skills from a job description using AI"""
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
def api_generate_roadmap(user_id: int, job_id: int, db: Session = Depends(get_db)):
    """Generate a personalized upskilling roadmap"""
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
        match_result["missing_skills"],
        job.title
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

@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process resume file (PDF or TXT)"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Extract text based on file type
        resume_text = extract_text_from_file(file.filename, file_content)
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Resume appears to be empty or too short")
        
        # Extract email and name
        email = extract_email_from_text(resume_text)
        if not email:
            email = "user@example.com"
        
        name = extract_name_from_filename(file.filename)
        
        # Extract skills using AI
        skills = extract_skills_from_resume(resume_text)
        
        # Create or get user
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            # Update existing user
            existing_user.name = name
            existing_user.skills = skills
            existing_user.resume_text = resume_text
            db.commit()
            db.refresh(existing_user)
            user = existing_user
        else:
            # Create new user
            user = models.User(
                email=email,
                name=name,
                skills=skills,
                resume_text=resume_text
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "skills": user.skills
            },
            "extracted_skills": skills,
            "file_type": file.filename.split('.')[-1].upper()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.post("/api/ai/bulk-extract-skills")
def bulk_extract_skills(limit: int = 10, db: Session = Depends(get_db)):
    """Extract skills for jobs that don't have them yet"""
    jobs = db.query(models.Job).filter(
        (models.Job.required_skills == None) | (models.Job.required_skills == [])
    ).limit(limit).all()
    
    results = []
    for job in jobs:
        try:
            skills = extract_skills_from_job(job.job_description or "")
            job.required_skills = skills
            db.commit()
            results.append({"job_id": job.id, "title": job.title, "skills_count": len(skills)})
        except Exception as e:
            results.append({"job_id": job.id, "title": job.title, "error": str(e)})
    
    return {"processed": len(results), "jobs": results}

@app.get("/")
def root():
    return {
        "message": "Job Match Platform API",
        "docs": "/docs",
        "total_jobs": "350+",
        "status": "active"
    }
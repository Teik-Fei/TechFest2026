from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class JobBase(BaseModel):
    title: str
    company: str
    location: str
    employment_type: Optional[str] = None
    salary: Optional[str] = None

class Job(JobBase):
    id: int
    job_description: Optional[str] = None
    url: Optional[str] = None
    required_skills: Optional[List[str]] = []
    posted: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: str
    name: str
    skills: List[str]
    resume_text: Optional[str] = None

class User(UserCreate):
    id: int
    
    class Config:
        from_attributes = True

class ApplicationCreate(BaseModel):
    user_id: int
    job_id: int
    status: str = "applied"
    notes: Optional[str] = None

class Application(ApplicationCreate):
    id: int
    applied_at: datetime
    
    class Config:
        from_attributes = True

class SkillMatchResponse(BaseModel):
    job_id: int
    job_title: str
    match_percentage: float
    matching_skills: List[str]
    missing_skills: List[str]
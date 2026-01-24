from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from database import Base
from datetime import datetime

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    location = Column(String)
    posted = Column(String)
    workplace_model = Column(String)
    employment_type = Column(String)
    salary = Column(String)
    job_description = Column(Text)
    job_id = Column(String, unique=True)
    url = Column(String)
    required_skills = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    skills = Column(JSON)
    resume_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    status = Column(String, default="applied")
    applied_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)


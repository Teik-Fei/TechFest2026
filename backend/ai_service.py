from groq import Groq
import os
from typing import List, Dict
from dotenv import load_dotenv
import json
import re

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)

def extract_skills_from_job(job_description: str) -> List[str]:
    """Extract required skills from a job description using Groq AI"""
    prompt = f"""Extract all technical skills, qualifications, and requirements from this job description.
Return ONLY a JSON array of skills, nothing else.

Job Description:
{job_description}

Return format: ["skill1", "skill2", "skill3"]"""
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r'```json\n?|\n?```', '', content)
        skills = json.loads(content)
        return skills if isinstance(skills, list) else []
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return []

def calculate_skill_match(user_skills: List[str], job_skills: List[str]) -> Dict:
    """Calculate match percentage between user skills and job requirements"""
    if not job_skills:
        return {"match_percentage": 0, "matched_skills": [], "missing_skills": []}
    
    user_skills_lower = [s.lower() for s in user_skills]
    job_skills_lower = [s.lower() for s in job_skills]
    
    matched = [skill for skill in job_skills if skill.lower() in user_skills_lower]
    missing = [skill for skill in job_skills if skill.lower() not in user_skills_lower]
    
    match_percentage = (len(matched) / len(job_skills)) * 100 if job_skills else 0
    
    return {
        "match_percentage": round(match_percentage, 2),
        "matched_skills": matched,
        "missing_skills": missing
    }

def generate_upskilling_roadmap(user_skills: List[str], missing_skills: List[str], job_title: str) -> Dict:
    """Generate a personalized learning roadmap using Groq AI"""
    prompt = f"""Create a learning roadmap for someone who wants to become a {job_title}.
They already have these skills: {', '.join(user_skills)}
They need to learn: {', '.join(missing_skills)}

Return ONLY a JSON object with this exact structure:
{{
  "roadmap": [
    {{"skill": "skill_name", "priority": "High/Medium/Low", "estimated_time": "X weeks", "resources": ["resource1", "resource2"]}}
  ],
  "projects": ["project1", "project2"]
}}"""
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.5
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r'```json\n?|\n?```', '', content)
        roadmap = json.loads(content)
        return roadmap
    except Exception as e:
        print(f"Error generating roadmap: {e}")
        return {"roadmap": [], "projects": []}

def extract_skills_from_resume(resume_text: str) -> List[str]:
    """Extract skills from a resume text using Groq AI"""
    prompt = f"""Extract all technical skills, tools, and technologies mentioned in this resume.
Return ONLY a JSON array of skills, nothing else.

Resume:
{resume_text}

Return format: ["skill1", "skill2", "skill3"]"""
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r'```json\n?|\n?```', '', content)
        skills = json.loads(content)
        return skills if isinstance(skills, list) else []
    except Exception as e:
        print(f"Error extracting resume skills: {e}")
        return []
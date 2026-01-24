import openai
import os
from typing import List, Dict
from dotenv import load_dotenv
import json
import re

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_skills_from_job(job_description: str) -> List[str]:
    """Extract technical skills from job description"""
    if not job_description or len(job_description) < 50:
        return []
    
    prompt = f"""Extract all technical skills, programming languages, frameworks, tools, and technologies from this job description.
Return ONLY a JSON array of skills.

Job Description:
{job_description[:2000]}

Format: ["Python", "React", "AWS", "Docker", ...]"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r'```json\n?|\n?```', '', content)
        skills = json.loads(content)
        return skills[:15]
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return []

def calculate_skill_match(user_skills: List[str], job_skills: List[str]) -> Dict:
    """Calculate match percentage between user and job skills"""
    if not job_skills:
        return {
            "match_percentage": 0,
            "matching_skills": [],
            "missing_skills": [],
            "total_required": 0
        }
    
    user_skills_lower = [s.lower().strip() for s in user_skills]
    job_skills_lower = [s.lower().strip() for s in job_skills]
    
    matching = [s for s in job_skills if s.lower() in user_skills_lower]
    missing = [s for s in job_skills if s.lower() not in user_skills_lower]
    
    match_percentage = (len(matching) / len(job_skills) * 100) if job_skills else 0
    
    return {
        "match_percentage": round(match_percentage, 1),
        "matching_skills": matching,
        "missing_skills": missing,
        "total_required": len(job_skills)
    }

def generate_upskilling_roadmap(user_skills: List[str], target_job_title: str, missing_skills: List[str]) -> Dict:
    """Generate personalized learning roadmap"""
    if not missing_skills:
        return {
            "message": "You already have all required skills!",
            "courses": [],
            "projects": [],
            "timeline": "0 weeks"
        }
    
    prompt = f"""Create a learning roadmap for:
Current Skills: {', '.join(user_skills)}
Target Role: {target_job_title}
Skills to Learn: {', '.join(missing_skills[:5])}

Provide 3-5 specific courses and 2-3 project ideas. Return as JSON:
{{
    "courses": [
        {{"skill": "Python", "course": "Python Bootcamp", "duration": "4 weeks", "platform": "Coursera/Udemy"}},
    ],
    "projects": ["Build a REST API", "Create a portfolio website"],
    "timeline": "8-12 weeks",
    "difficulty": "Beginner/Intermediate/Advanced"
}}"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r'```json\n?|\n?```', '', content)
        roadmap = json.loads(content)
        return roadmap
    except Exception as e:
        print(f"Error generating roadmap: {e}")
        return {
            "error": str(e),
            "courses": [],
            "projects": [],
            "timeline": "N/A"
        }

def extract_skills_from_resume(resume_text: str) -> List[str]:
    """Extract skills from resume text"""
    prompt = f"""Extract all technical skills from this resume. Return ONLY a JSON array.

Resume:
{resume_text[:3000]}

Format: ["Python", "JavaScript", ...]"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r'```json\n?|\n?```', '', content)
        skills = json.loads(content)
        return skills
    except Exception as e:
        print(f"Error extracting resume skills: {e}")
        return []
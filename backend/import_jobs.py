import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Job
import uuid

# Create all tables
Base.metadata.create_all(bind=engine)

def import_jobs_from_csv():
    csv_path = "C:\\Users\\TeikFei\\Downloads\\Hackathons\\TechFest 2026\\all_jobs.csv"
    
    df = pd.read_csv(csv_path)
    db = SessionLocal()
    
    imported_count = 0
    skipped_count = 0
    
    for _, row in df.iterrows():
        try:
            # Get Job_Id or Jobid, if "Not Applicable" or empty, generate unique ID
            job_id_raw = row.get('Job_Id') or row.get('Jobid')
            if pd.isna(job_id_raw) or str(job_id_raw).strip() in ['Not Applicable', 'NOT FOUND', '']:
                job_id_val = f"generated_{uuid.uuid4().hex[:12]}"
            else:
                job_id_val = str(job_id_raw)
            
            # Check if already exists in DB
            existing = db.query(Job).filter(Job.job_id == job_id_val).first()
            if existing:
                skipped_count += 1
                continue
            
            job = Job(
                title=str(row.get('Title', '')),
                company=str(row.get('Company', '')),
                location=str(row.get('Location', '')),
                posted=str(row.get('Posted', row.get('Posted_Date', ''))),
                workplace_model=str(row.get('Workplace_Model', '')),
                employment_type=str(row.get('Employment_Type', row.get('Type', ''))),
                salary=str(row.get('Salary', '')),
                job_description=str(row.get('Description', '')),
                job_id=job_id_val,
                url=str(row.get('Url', '')),
                required_skills=[]
            )
            db.add(job)
            db.commit()
            imported_count += 1
        except Exception as e:
            db.rollback()
            skipped_count += 1
            print(f"⏭️  Skipping: {row.get('Title', 'Unknown')} - {e}")
    
    db.close()
    print(f"✅ Successfully imported {imported_count} jobs!")
    print(f"⏭️  Skipped {skipped_count} jobs (duplicates or errors)")

if __name__ == "__main__":
    import_jobs_from_csv()
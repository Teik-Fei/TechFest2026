import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Job

# Create all tables
Base.metadata.create_all(bind=engine)

def import_jobs_from_csv():
    # Use the actual CSV file path
    csv_path = r"c:\Users\zheqi\Downloads\techfest\efinancialcareers.csv"
    
    df = pd.read_csv(csv_path)
    db = SessionLocal()
    
    imported_count = 0
    for _, row in df.iterrows():
        try:
            job = Job(
                title=str(row.get('title', '')),
                company=str(row.get('company', '')),
                location=str(row.get('location', '')),
                posted=str(row.get('posted', '')),
                workplace_model=str(row.get('workplace_model', '')),
                employment_type=str(row.get('employment_type', '')),
                salary=str(row.get('salary', '')),
                job_description=str(row.get('job_description', '')),
                job_id=str(row.get('jobId', f'job_{row.name}')),
                url=str(row.get('url', '')),
                required_skills=[]
            )
            db.add(job)
            imported_count += 1
        except Exception as e:
            print(f"Error importing job {row.get('title', 'Unknown')}: {e}")
    
    db.commit()
    db.close()
    print(f"✅ Successfully imported {imported_count} jobs!")

if __name__ == "__main__":
    import_jobs_from_csv()
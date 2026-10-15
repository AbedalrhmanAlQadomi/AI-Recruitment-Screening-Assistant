import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from src.job_description import load_job_description, save_job_description
from src.ai_extractor import extract_job_requirements
from src.ranking import load_results, filter_and_rank_candidates, update_candidate_status
from main import run_pipeline

app = FastAPI(title="Recruitment Screening Assistant API")

class JobCreate(BaseModel):
    content: str

class StatusUpdate(BaseModel):
    status: str

@app.post("/jobs")
def create_job(job: JobCreate):
    if not job.content.strip():
        raise HTTPException(status_code=400, detail="Job content cannot be empty")
    save_job_description(job.content)
    extracted = extract_job_requirements(job.content)
    return {"message": "Job created successfully", "requirements": extracted}

@app.get("/jobs")
def get_job():
    try:
        content = load_job_description()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/jobs/extract")
def extract_requirements():
    try:
        content = load_job_description()
        return extract_job_requirements(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/screen")
def trigger_screening():
    try:
        result = run_pipeline()
        return {"message": "Screening completed", "stats": result["stats"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/candidates")
def get_candidates(top_n: int = 20):
    results = load_results()
    return filter_and_rank_candidates(results, top_n=top_n)

@app.get("/candidates/{index}")
def get_candidate(index: int):
    results = load_results()
    if 0 <= index < len(results):
        return results[index]
    raise HTTPException(status_code=404, detail="Candidate not found")

@app.post("/candidates/{index}/status")
def set_status(index: int, payload: StatusUpdate):
    if payload.status not in ["Shortlist", "Review Later", "Reject", "Pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    success = update_candidate_status(index, payload.status)
    if not success:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": f"Candidate status updated to {payload.status}"}

@app.get("/candidates/{index}/cv")
def get_candidate_cv(index: int):
    results = load_results()
    if 0 <= index < len(results):
        file_path = results[index].get("cv_file_path")
        if file_path and os.path.exists(file_path):
            return FileResponse(file_path, filename=os.path.basename(file_path))
        raise HTTPException(status_code=404, detail="CV file not found")
    raise HTTPException(status_code=404, detail="Candidate not found")
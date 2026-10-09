import os

def load_job_description(file_path="data/jobs/sample_job.txt"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        
    if not content:
        raise ValueError(f"Empty job description: {file_path}")
        
    return content

def save_job_description(content, file_path="data/jobs/sample_job.txt"):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content.strip())
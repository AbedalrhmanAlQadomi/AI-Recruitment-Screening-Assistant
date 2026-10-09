import json
import os
import re
from dotenv import load_dotenv
import ollama

load_dotenv()

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b") 

def clean_json_response(raw_text):
    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    try:
        return json.loads(raw_text)
    except Exception:
        return {}

def extract_job_requirements(job_text, model=DEFAULT_MODEL):
    prompt = f"""
Extract requirements from this Job Description into a JSON object:
Job Description:
{job_text}

JSON structure:
{{
    "must_have": ["list of essential requirements"],
    "nice_to_have": ["list of optional requirements"],
    "skills": ["list of required skills"],
    "experience": "experience requirement",
    "education": "education requirement",
    "languages": ["list of languages"],
    "certifications": ["list of certifications"]
}}
"""
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], format="json")
    return clean_json_response(response["message"]["content"])

def extract_candidate_info(cv_text, model=DEFAULT_MODEL):
    prompt = f"""
Extract candidate information from this CV into a JSON object:
CV Content:
{cv_text}

JSON structure:
{{
    "candidate_name": "name",
    "skills": ["list of candidate skills"],
    "work_experience": ["list of experience details"],
    "education": ["list of education details"],
    "languages": ["list of languages"],
    "certifications": ["list of certifications"]
}}
"""
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], format="json")
    return clean_json_response(response["message"]["content"])



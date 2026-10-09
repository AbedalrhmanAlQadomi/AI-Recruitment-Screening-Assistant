import json
import os
from src.gmail import get_gmail_service
from src.email_processor import search_emails, parse_email_message, load_processed_ids, save_processed_id
from src.cv_processor import download_attachment, extract_cv_text
from src.job_description import load_job_description
from src.ai_extractor import extract_job_requirements, extract_candidate_info
from src.matcher import match_candidate

def run_pipeline():
    service = get_gmail_service()
    processed_ids = load_processed_ids()
    job_text = load_job_description()
    job_data = extract_job_requirements(job_text)
    
    results_file = "data/processed-fake-cv/results.json"
    results = []
    if os.path.exists(results_file):
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = []

    messages = search_emails(service)

    for msg in messages:
        msg_id = msg['id']
        if msg_id in processed_ids:
            continue
        
        email_data = parse_email_message(service, msg_id)
        for attachment in email_data.get('attachments', []):
            file_path = download_attachment(service, msg_id, attachment['attachment_id'], attachment['filename'])
            cv_text = extract_cv_text(file_path)
            if not cv_text:
                continue
            
            candidate_info = extract_candidate_info(cv_text)
            match_res = match_candidate(job_data, candidate_info, cv_text)
            match_res['email_id'] = msg_id
            match_res['candidate_email'] = email_data['sender']
            
            candidate_entry = {"---": "#################################################################################"}
            candidate_entry.update(match_res)
            results.append(candidate_entry)
            
        save_processed_id(msg_id)

    results.sort(key=lambda x: (x.get('is_qualified', False), x.get('overall_score', 0)), reverse=True)
    
    os.makedirs("data/processed-fake-cv", exist_ok=True)
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_pipeline()
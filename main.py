import os
from src.gmail import get_gmail_service
from src.email_processor import search_emails, parse_email_message, load_processed_ids, save_processed_id
from src.cv_processor import download_attachment, extract_cv_text
from src.job_description import load_job_description
from src.ai_extractor import extract_job_requirements, extract_candidate_info
from src.matcher import match_candidate
from src.ranking import load_results, save_results, filter_and_rank_candidates

def run_pipeline():
    print("Starting pipeline...")
    service = get_gmail_service()
    processed_ids = load_processed_ids()
    job_text = load_job_description()
    job_data = extract_job_requirements(job_text)
    job_keyword = job_data.get("job_title")
    
    results = load_results()
    existing_emails = {r.get("email_id") for r in results if "email_id" in r}

    messages = search_emails(service, job_keyword=job_keyword)
    print(f"Found {len(messages)} messages")

    for msg in messages:
        msg_id = msg['id']
        if msg_id in processed_ids or msg_id in existing_emails:
            continue
        
        email_data = parse_email_message(service, msg_id)
        for attachment in email_data.get('attachments', []):
            file_path = download_attachment(service, msg_id, attachment['attachment_id'], attachment['filename'])
            cv_text = extract_cv_text(file_path)
            if not cv_text:
                continue
            
            candidate_info = extract_candidate_info(cv_text)
            match_res = match_candidate(job_data, candidate_info, cv_text, file_path=file_path)
            match_res['email_id'] = msg_id
            match_res['candidate_email'] = email_data['sender']
            match_res['hr_status'] = "Pending"
            
            missing_must = [r["requirement"] for r in match_res.get("must_have_evaluations", []) if r["status"] == "Does Not Meet"]
            match_res['missing_must_haves'] = missing_must
            
            results.append(match_res)
            print(f"Processed: {match_res['candidate_name']}")
            
        save_processed_id(msg_id)

    ranked_data = filter_and_rank_candidates(results)
    sorted_all = ranked_data["qualified"] + ranked_data["unqualified"]
    save_results(sorted_all)
    print("Pipeline completed")
    return ranked_data

if __name__ == "__main__":
    run_pipeline()
import os
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import ollama
from src.ai_extractor import DEFAULT_MODEL, clean_json_response

embed_model = None

def get_embed_model():
    global embed_model
    if embed_model is None:
        model_name = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
        embed_model = SentenceTransformer(model_name)
    return embed_model

def calculate_similarity(text_a, text_b):
    if not text_a or not text_b or text_b == "No evidence found":
        return 0.0
    model = get_embed_model()
    emb_a = model.encode([text_a])
    emb_b = model.encode([text_b])
    return float(cosine_similarity(emb_a, emb_b)[0][0])

def rule_based_check(requirement, candidate_data):
    req_lower = requirement.lower()
    candidate_skills = [s.lower() for s in candidate_data.get("skills", [])]
    candidate_edu = " ".join(candidate_data.get("education", [])).lower()
    candidate_exp = " ".join(candidate_data.get("work_experience", [])).lower()
    candidate_langs = [l.lower() for l in candidate_data.get("languages", [])]
    candidate_certs = [c.lower() for c in candidate_data.get("certifications", [])]

    for skill in candidate_skills:
        if skill and skill in req_lower:
            return True

    for cert in candidate_certs:
        if cert and cert in req_lower:
            return True

    for lang in candidate_langs:
        if lang and lang in req_lower:
            return True

    edu_keywords = ["degree", "bachelor", "master", "phd", "computer science", "software", "engineering", "information"]
    if any(k in req_lower for k in edu_keywords):
        if any(k in candidate_edu for k in edu_keywords):
            return True

    exp_keywords = ["year", "years", "experience", "hands-on"]
    if any(k in req_lower for k in exp_keywords) and len(candidate_exp) > 20:
        return True

    return False

def evaluate_requirement(requirement, candidate_data, raw_cv_text, model=DEFAULT_MODEL):
    prompt = f"""
Evaluate if the candidate meets the following job requirement based ONLY on the provided CV text.
If there is not enough information, state that no evidence was found.

Requirement: {requirement}
CV Text: {raw_cv_text}

JSON structure:
{{
    "status": "Meets | Partially Meets | Does Not Meet",
    "evidence": "direct quote or explanation from CV, or 'No evidence found'"
}}
"""
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], format="json")
    res = clean_json_response(response["message"]["content"])
    
    status = res.get("status", "Does Not Meet")
    if status not in ["Meets", "Partially Meets", "Does Not Meet"]:
        status = "Does Not Meet"
        
    evidence = res.get("evidence", "No evidence found")
    if not evidence or evidence.lower() == "none":
        evidence = "No evidence found"
        status = "Does Not Meet"

    similarity = calculate_similarity(requirement, evidence)
    rule_matched = rule_based_check(requirement, candidate_data)

    if evidence == "No evidence found":
        status = "Does Not Meet"
        similarity = 0.0

    return {
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "rule_match": rule_matched,
        "similarity_score": round(similarity, 4)
    }

def match_candidate(job_data, candidate_data, raw_cv_text, file_path="", model=DEFAULT_MODEL):
    must_have_list = job_data.get("must_have", [])
    nice_to_have_list = job_data.get("nice_to_have", [])
    
    must_results = [evaluate_requirement(req, candidate_data, raw_cv_text, model) for req in must_have_list]
    nice_results = [evaluate_requirement(req, candidate_data, raw_cv_text, model) for req in nice_to_have_list]
    
    has_failed_must_have = any(r["status"] == "Does Not Meet" for r in must_results)
    is_qualified = not has_failed_must_have
     
    score_map = {"Meets": 1.0, "Partially Meets": 0.5, "Does Not Meet": 0.0}
    all_results = must_results + nice_results
    
    total_score = sum(
        score_map[r["status"]] + (0.2 * r["similarity_score"]) + (0.1 if r["rule_match"] else 0.0)
        for r in all_results
    ) if all_results else 0.0

    return {
        "candidate_name": candidate_data.get("candidate_name", "Unknown"),
        "cv_file_path": file_path,
        "is_qualified": is_qualified,
        "overall_score": round(total_score, 2),
        "must_have_evaluations": must_results,
        "nice_to_have_evaluations": nice_results
    }
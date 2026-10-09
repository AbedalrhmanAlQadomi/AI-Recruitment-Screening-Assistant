import os
import json
import numpy as np
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
    if not text_a or not text_b:
        return 0.0
    model = get_embed_model()
    emb_a = model.encode([text_a])
    emb_b = model.encode([text_b])
    return float(cosine_similarity(emb_a, emb_b)[0][0])

def evaluate_requirement(requirement, cv_text, model=DEFAULT_MODEL):
    prompt = f"""
Evaluate if the candidate meets the following job requirement based ONLY on the provided CV text.
If there is not enough information, state that no evidence was found.

Requirement: {requirement}
CV Text: {cv_text}

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
    similarity = calculate_similarity(requirement, evidence if evidence != "No evidence found" else cv_text[:500])
    
    return {
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "similarity_score": round(similarity, 4)
    }

def match_candidate(job_data, candidate_data, raw_cv_text, model=DEFAULT_MODEL):
    must_have_list = job_data.get("must_have", [])
    nice_to_have_list = job_data.get("nice_to_have", [])
    
    must_results = [evaluate_requirement(req, raw_cv_text, model) for req in must_have_list]
    nice_results = [evaluate_requirement(req, raw_cv_text, model) for req in nice_to_have_list]
    
    has_failed_must_have = any(r["status"] == "Does Not Meet" for r in must_results)
    is_qualified = not has_failed_must_have
    
    score_map = {"Meets": 1.0, "Partially Meets": 0.5, "Does Not Meet": 0.0}
    all_results = must_results + nice_results
    total_score = sum(score_map[r["status"]] + (0.2 * r["similarity_score"]) for r in all_results) if all_results else 0.0
    
    return {
        "candidate_name": candidate_data.get("candidate_name", "Unknown"),
        "is_qualified": is_qualified,
        "overall_score": round(total_score, 2),
        "must_have_evaluations": must_results,
        "nice_to_have_evaluations": nice_results
    }
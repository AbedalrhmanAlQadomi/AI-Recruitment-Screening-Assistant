import json
import os
import pandas as pd

RESULTS_FILE = "data/processed-fake-cv/results.json"

def load_results(filepath=RESULTS_FILE):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_results(results, filepath=RESULTS_FILE):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def filter_and_rank_candidates(results, top_n=20):
    if not results:
        return {
            "qualified": [],
            "unqualified": [],
            "shortlist": [],
            "stats": {"total": 0, "qualified": 0, "unqualified": 0}
        }
    
    df = pd.DataFrame(results)
    
    for col in ["is_qualified", "overall_score"]:
        if col not in df.columns:
            df[col] = False if col == "is_qualified" else 0.0

    df_qualified = df[df["is_qualified"] == True].sort_values(by="overall_score", ascending=False)
    df_unqualified = df[df["is_qualified"] == False].sort_values(by="overall_score", ascending=False)
    
    df_shortlist = df_qualified.head(top_n)
    
    return {
        "qualified": df_qualified.to_dict(orient="records"),
        "unqualified": df_unqualified.to_dict(orient="records"),
        "shortlist": df_shortlist.to_dict(orient="records"),
        "stats": {
            "total": len(df),
            "qualified": len(df_qualified),
            "unqualified": len(df_unqualified)
        }
    }

def update_candidate_status(candidate_idx, new_status, filepath=RESULTS_FILE):
    results = load_results(filepath)
    if 0 <= candidate_idx < len(results):
        results[candidate_idx]["hr_status"] = new_status
        save_results(results, filepath)
        return True
    return False
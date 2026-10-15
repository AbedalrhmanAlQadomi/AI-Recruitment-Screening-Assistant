import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.ranking import filter_and_rank_candidates
from src.cv_processor import clean_text

client = TestClient(app)

def test_get_job():
    response = client.get("/jobs")
    assert response.status_code in [200, 404]

def test_create_job_invalid():
    response = client.post("/jobs", json={"content": "   "})
    assert response.status_code == 400

def test_clean_text():
    raw = "Hello   world \n test  "
    assert clean_text(raw) == "Hello world test"

def test_filter_and_rank():
    mock_data = [
        {"candidate_name": "Alice", "is_qualified": True, "overall_score": 8.5},
        {"candidate_name": "Bob", "is_qualified": False, "overall_score": 9.0},
        {"candidate_name": "Charlie", "is_qualified": True, "overall_score": 7.0}
    ]
    ranked = filter_and_rank_candidates(mock_data, top_n=1)
    assert len(ranked["shortlist"]) == 1
    assert ranked["shortlist"][0]["candidate_name"] == "Alice"
    assert ranked["stats"]["total"] == 3
    assert ranked["stats"]["qualified"] == 2
    assert ranked["stats"]["unqualified"] == 1

def test_invalid_status_update():
    response = client.post("/candidates/0/status", json={"status": "InvalidStatus"})
    assert response.status_code == 400
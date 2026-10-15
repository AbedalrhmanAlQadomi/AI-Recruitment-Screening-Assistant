# AI Recruitment Screening Assistant
An AI-driven system to screen CVs received via Gmail against job descriptions using Ollama, Sentence Transformers, FastAPI, and Streamlit.
 
 
# Features
Fetches and parses CVs (PDF/DOCX) from Gmail.
Extracts job requirements and candidate data using Ollama.
Matches candidates via Rule-Based checks and Semantic Similarity.
Filters Must-Have criteria and ranks candidates with Pandas.
REST API powered by FastAPI.
Interactive HR dashboard built with Streamlit.

##
your Google Cloud OAuth credentials.json inside the credentials/ folder.

# model 
OLLAMA_MODEL=qwen3:8b

## Run
# Backend API
.venv\Scripts\activate
uvicorn src.api:app --reload --port 8000

# Streamlit
.venv\Scripts\activate
streamlit run app.py

# for test 
python -m pytest




## stop run 
Stop-Process -Name "python" -Force

# Installation
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
 




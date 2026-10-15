import os
import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Recruitment Assistant", layout="wide")
st.title("AI Recruitment Screening Assistant")

page = st.sidebar.radio("Navigation", ["Job Management", "Screening & Rankings", "Candidate Review"])

if page == "Job Management":
    st.header("Job Description & Requirements")
    default_text = ""
    try:
        res = requests.get(f"{API_URL}/jobs")
        if res.status_code == 200:
            default_text = res.json().get("content", "")
    except Exception:
        pass

    job_text = st.text_area("Enter Job Description", value=default_text, height=250)
    
    if st.button("Save Job & Extract Requirements"):
        if not job_text.strip():
            st.error("Job description cannot be empty.")
        else:
            with st.spinner("Processing..."):
                try:
                    res = requests.post(f"{API_URL}/jobs", json={"content": job_text})
                    if res.status_code == 200:
                        st.success("Job saved and requirements extracted.")
                        st.session_state["extracted_reqs"] = res.json().get("requirements", {})
                    else:
                        st.error("Failed to process job.")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    if "extracted_reqs" in st.session_state:
        reqs = st.session_state["extracted_reqs"]
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Must-Have Requirements")
            st.write(reqs.get("must_have", []))
            st.subheader("Required Skills")
            st.write(reqs.get("skills", []))
        with col2:
            st.subheader("Nice-to-Have Requirements")
            st.write(reqs.get("nice_to_have", []))
            st.subheader("Education & Experience")
            st.write(f"Education: {reqs.get('education')}")
            st.write(f"Experience: {reqs.get('experience')}")

elif page == "Screening & Rankings":
    st.header("Screening & Candidate Rankings")
    
    if st.button("Start CV Screening"):
        with st.spinner("Screening CVs from Gmail..."):
            try:
                res = requests.post(f"{API_URL}/screen")
                if res.status_code == 200:
                    st.success("Screening finished successfully.")
                else:
                    st.error("Screening failed.")
            except Exception as e:
                st.error(f"API Error: {e}")

    top_n = st.slider("Shortlist Count (Top N)", min_value=1, max_value=50, value=20)
    
    try:
        res = requests.get(f"{API_URL}/candidates", params={"top_n": top_n})
        if res.status_code == 200:
            data = res.json()
            stats = data.get("stats", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Candidates", stats.get("total", 0))
            c2.metric("Qualified Candidates", stats.get("qualified", 0))
            c3.metric("Unqualified Candidates", stats.get("unqualified", 0))

            shortlist = data.get("shortlist", [])
            st.subheader(f"Top {top_n} Qualified Candidates")
            if shortlist:
                df = pd.DataFrame(shortlist)[["candidate_name", "candidate_email", "overall_score", "hr_status"]]
                df.columns = ["Name", "Email", "Score", "HR Status"]
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No qualified candidates found yet.")
                
            unqualified = data.get("unqualified", [])
            if unqualified:
                with st.expander("View Unqualified Candidates"):
                    df_unq = pd.DataFrame(unqualified)[["candidate_name", "candidate_email", "overall_score", "missing_must_haves"]]
                    st.dataframe(df_unq, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to fetch candidates: {e}")

elif page == "Candidate Review":
    st.header("Candidate Review & Decision")
    try:
        res = requests.get(f"{API_URL}/candidates")
        if res.status_code == 200:
            candidates = res.json().get("qualified", []) + res.json().get("unqualified", [])
            if not candidates:
                st.info("No candidates available for review.")
            else:
                names = [f"{i}: {c.get('candidate_name')} ({c.get('hr_status', 'Pending')})" for i, c in enumerate(candidates)]
                selected_idx = st.selectbox("Select Candidate", range(len(names)), format_func=lambda x: names[x])
                cand = candidates[selected_idx]

                st.subheader(f"Candidate: {cand.get('candidate_name')}")
                st.write(f"**Email:** {cand.get('candidate_email')}")
                st.write(f"**Score:** {cand.get('overall_score')}")
                st.write(f"**Current Status:** {cand.get('hr_status', 'Pending')}")
                st.write(f"**Qualified:** {cand.get('is_qualified')}")

                if cand.get("missing_must_haves"):
                    st.error(f"Missing Must-Haves: {', '.join(cand.get('missing_must_haves'))}")

                cv_path = cand.get("cv_file_path", "")
                if cv_path and os.path.exists(cv_path):
                    with open(cv_path, "rb") as f:
                        st.download_button("Download Original CV", f, file_name=os.path.basename(cv_path))

                st.subheader("Evaluations")
                evals = cand.get("must_have_evaluations", []) + cand.get("nice_to_have_evaluations", [])
                if evals:
                    df_evals = pd.DataFrame(evals)[["requirement", "status", "evidence", "similarity_score", "rule_match"]]
                    st.dataframe(df_evals, use_container_width=True)

                st.subheader("HR Decision")
                col1, col2, col3 = st.columns(3)
                if col1.button("Shortlist"):
                    requests.post(f"{API_URL}/candidates/{selected_idx}/status", json={"status": "Shortlist"})
                    st.rerun()
                if col2.button("Review Later"):
                    requests.post(f"{API_URL}/candidates/{selected_idx}/status", json={"status": "Review Later"})
                    st.rerun()
                if col3.button("Reject"):
                    requests.post(f"{API_URL}/candidates/{selected_idx}/status", json={"status": "Reject"})
                    st.rerun()
    except Exception as e:
        st.error(f"API Error: {e}")
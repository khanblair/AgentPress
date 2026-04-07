"""
ui/app.py — AgentPress Streamlit UI
"""

import streamlit as st
import requests
import time
import os

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="AgentPress", layout="wide")

st.title("🚀 AgentPress")
st.subheader("Brand-Aware Autonomous Document Creation Pipeline")

with st.sidebar:
    st.header("Project Context")
    session_id = st.text_input("Session ID", value="default_session")
    
    st.divider()
    st.header("Brand Assets")
    uploaded_file = st.file_uploader("Upload Brand PDF or PPTX", type=["pdf", "pptx"])
    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")

# Main generation panel
st.header("Document Generation")
user_prompt = st.text_area("Enter your document request (e.g., 'Create a 5-slide investor deck for a fintech startup')", height=150)

if st.button("Generate Document", type="primary"):
    if not user_prompt:
        st.error("Please enter a prompt.")
    else:
        with st.spinner("Agent team is planning, researching, and drafting..."):
            try:
                resp = requests.post(f"{API_URL}/generate", json={"prompt": user_prompt, "session_id": session_id})
                resp.raise_for_status()
                job = resp.json()
                job_id = job["job_id"]
                
                # Polling for status
                status_placeholder = st.empty()
                progress_bar = st.progress(0)
                
                for i in range(1, 101):
                    time.sleep(2) # Polling interval
                    status_resp = requests.get(f"{API_URL}/status/{job_id}")
                    status_data = status_resp.json()
                    
                    current_status = status_data.get("status", "unknown")
                    current_node = status_data.get("current_node", "initializing")
                    
                    status_placeholder.info(f"Status: **{current_status.upper()}** | Current Agent: **{current_node.capitalize()}**")
                    progress_bar.progress(min(i * 5, 100))
                    
                    if current_status == "completed":
                        st.balloons()
                        st.success("Document generated successfully!")
                        file_path = status_data.get("file_path")
                        if file_path and os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                st.download_button("Download Document", f, file_name=os.path.basename(file_path))
                        break
                    elif current_status == "failed":
                        st.error(f"Generation failed: {status_data.get('error')}")
                        break
            except Exception as e:
                st.error(f"Communication error with backend: {e}")

# Correction loop panel
st.divider()
st.header("Evolution Engine (Human-in-the-loop Correction)")
col1, col2 = st.columns(2)

with col1:
    original_text = st.text_area("Original AI Output", height=200)
with col2:
    corrected_text = st.text_area("Your Corrected Version", height=200)

if st.button("Submit Correction for Self-Improvement"):
    if not original_text or not corrected_text:
        st.warning("Please provide both versions to compute the delta.")
    else:
        try:
            resp = requests.post(f"{API_URL}/submit-correction", json={
                "original": original_text,
                "corrected": corrected_text,
                "session_id": session_id
            })
            resp.raise_for_status()
            st.success("Correction processed! Agent 6 (Meta-Engineer) is updating the brand rules.")
        except Exception as e:
            st.error(f"Failed to submit correction: {e}")

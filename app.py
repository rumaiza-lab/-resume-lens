"""Streamlit UI for analyzing resumes against a target role with Groq."""

from __future__ import annotations

import json
import os
from typing import Any

import pymupdf
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = "qwen/qwen3.6-27b"
MAX_RESUME_CHARS = 45_000


def extract_pdf_text(uploaded_file: Any) -> str:
    """Extract readable text from every page in an uploaded PDF."""
    document = pymupdf.open(stream=uploaded_file.getvalue(), filetype="pdf")
    pages = [page.get_text("text") for page in document]
    document.close()
    return "\n".join(pages).strip()


def build_prompt(job_role: str, resume_text: str) -> str:
    return f"""You are an experienced technical recruiter. Analyze the resume below for the target role.

Target role or job description:
{job_role}

Resume text:
{resume_text[:MAX_RESUME_CHARS]}

Return valid JSON only with this exact structure:
{{
  "candidate_summary": "2-4 sentence summary",
  "match_score": 0,
  "matching_skills": ["skill 1"],
  "missing_or_weak_skills": ["skill 1"],
  "relevant_experience": ["evidence from the resume"],
  "concerns": ["specific concern or empty array"],
  "interview_questions": ["question 1", "question 2", "question 3"],
  "recommendation": "Strong fit, Potential fit, or Not a fit",
  "recommendation_reason": "short evidence-based explanation"
}}

Use a whole-number match_score from 0 to 100. Do not invent experience that is not present in the resume."""


def parse_json_response(content: str) -> dict[str, Any]:
    """Parse a JSON object even when the model adds Markdown or a short preface."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

    object_start = cleaned.find("{")
    if object_start == -1:
        raise json.JSONDecodeError("No JSON object found", cleaned, 0)

    result, _ = json.JSONDecoder().raw_decode(cleaned[object_start:])
    if not isinstance(result, dict):
        raise json.JSONDecodeError("Expected a JSON object", cleaned, object_start)
    return result


def fallback_result(content: str) -> dict[str, Any]:
    """Keep a useful plain-text model response visible if JSON generation fails."""
    return {
        "candidate_summary": content.strip() or "The model returned an empty response.",
        "match_score": "N/A",
        "matching_skills": [],
        "missing_or_weak_skills": [],
        "relevant_experience": [],
        "concerns": ["The model response was not valid JSON; review the summary below."],
        "interview_questions": [],
        "recommendation": "Review manually",
        "recommendation_reason": "The raw model response is shown as the candidate summary.",
    }


def analyze_resume(client: Groq, model: str, job_role: str, resume_text: str) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        max_tokens=900,
        messages=[
            {
                "role": "system",
                "content": "You are a precise resume screening assistant. Follow the requested JSON schema exactly.",
            },
            {"role": "user", "content": build_prompt(job_role, resume_text)},
        ],
    )
    content = response.choices[0].message.content or "{}"
    try:
        return parse_json_response(content)
    except json.JSONDecodeError:
        return fallback_result(content)


def render_result(file_name: str, result: dict[str, Any]) -> None:
    st.subheader(file_name)
    score = result.get("match_score", "N/A")
    recommendation = result.get("recommendation", "N/A")
    st.metric("Match score", f"{score}/100", delta=recommendation)
    st.write(result.get("candidate_summary", "No summary returned."))

    columns = st.columns(2)
    with columns[0]:
        st.markdown("**Matching skills**")
        st.write("\n".join(f"- {item}" for item in result.get("matching_skills", [])) or "None identified")
        st.markdown("**Relevant experience**")
        st.write("\n".join(f"- {item}" for item in result.get("relevant_experience", [])) or "None identified")
    with columns[1]:
        st.markdown("**Missing or weak skills**")
        st.write("\n".join(f"- {item}" for item in result.get("missing_or_weak_skills", [])) or "None identified")
        st.markdown("**Concerns**")
        st.write("\n".join(f"- {item}" for item in result.get("concerns", [])) or "None identified")

    st.markdown("**Suggested interview questions**")
    st.write("\n".join(f"- {item}" for item in result.get("interview_questions", [])) or "None returned")
    st.info(result.get("recommendation_reason", "No recommendation reason returned."))


st.set_page_config(page_title="Resume Lens", page_icon="📄", layout="wide")
st.title("Resume Lens")
st.caption("Screen resumes against a role with a Groq-hosted Qwen model.")

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "Groq API key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        help="Stored only in this session when entered here. For local development, use a .env file.",
    )
    model = st.text_input("Groq model", value=os.getenv("GROQ_MODEL", DEFAULT_MODEL))
    st.caption("Default: qwen/qwen3.6-27b. Change this if your Groq account exposes a different Qwen model.")

job_role = st.text_area(
    "Target job role or job description",
    placeholder="Example: Senior Python Backend Engineer with FastAPI, PostgreSQL, AWS, and mentoring experience",
    height=140,
)
uploaded_files = st.file_uploader(
    "Upload resume PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    help="Upload one or more text-based PDF resumes.",
)

analyze = st.button("Analyze resumes", type="primary", use_container_width=True)

if analyze:
    if not api_key:
        st.error("Add a Groq API key in the sidebar or GROQ_API_KEY in your .env file.")
    elif not job_role.strip():
        st.error("Enter a target role or job description first.")
    elif not uploaded_files:
        st.error("Upload at least one PDF resume first.")
    else:
        client = Groq(api_key=api_key)
        for uploaded_file in uploaded_files:
            with st.spinner(f"Analyzing {uploaded_file.name}..."):
                try:
                    resume_text = extract_pdf_text(uploaded_file)
                    if not resume_text:
                        st.warning(f"{uploaded_file.name} has no extractable text. Skipping it.")
                        continue
                    result = analyze_resume(client, model, job_role.strip(), resume_text)
                    render_result(uploaded_file.name, result)
                except Exception as error:
                    st.error(f"{uploaded_file.name}: {error}")

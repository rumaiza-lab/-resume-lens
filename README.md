# Resume Lens

Resume Lens is a Streamlit application that compares one or more resume PDFs against a target job role or job description. It extracts text locally with PyMuPDF, sends the extracted content to a Groq-hosted Qwen model, and renders a structured screening report.

## Features

- Upload one or more PDF resumes.
- Enter a target role or full job description.
- Analyze resumes with the Groq API and a configurable Qwen model.
- Return a match score, strengths, missing skills, concerns, evidence, interview questions, and hiring recommendation.
- Keep the API key in a local `.env` file or enter it in the sidebar.

## Architecture

```text
Streamlit UI
    |
    +-- PDF uploader + target role input
    |
    +-- PyMuPDF text extraction
    |
    +-- Prompt builder with resume and role context
    |
    +-- Groq chat completion (Qwen model)
    |
    +-- JSON parsing + result renderer
```

The application is intentionally small and stateless. PDF text extraction happens in the app process. The extracted text is sent to Groq only after the user presses **Analyze resumes**. The model name can be changed with `GROQ_MODEL` or the sidebar field.

## Workflow

1. Start the Streamlit app.
2. Add a Groq API key through `.env` or the sidebar.
3. Enter the target role or paste the job description.
4. Upload one or more text-based PDF resumes.
5. Press **Analyze resumes**.
6. Review each resume's score, evidence, gaps, concerns, questions, and recommendation.

## Setup on Windows

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace `your_groq_api_key_here` with a Groq API key. The default model is `qwen/qwen3.6-27b`; set `GROQ_MODEL` to another model available to your Groq account if needed.

## Run

```powershell
streamlit run app.py
```

Then open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Deploy on Streamlit Community Cloud

Streamlit Community Cloud provides a free hosting tier for public GitHub repositories.

1. Create a GitHub repository and push this project folder to it.
2. Do not commit `.env`; it is excluded by `.gitignore`.
3. Open [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
4. Select **New app**, choose the repository and branch, and set the main file to `app.py`.
5. Open **Advanced settings**, choose Python 3.11, and add these app secrets:

```toml
GROQ_API_KEY = "gsk_your_actual_key_here"
GROQ_MODEL = "qwen/qwen3.6-27b"
```

6. Click **Deploy**. Community Cloud installs packages from `requirements.txt` automatically.

After deployment, use the generated `streamlit.app` URL. Never put the Groq key in GitHub files or the repository README.

## Validate

```powershell
python -m py_compile app.py
```

## Notes

- The app expects text-based PDFs. Scanned image-only PDFs need OCR before analysis.
- Resume text is truncated before prompting to keep requests within model context limits.
- Do not commit `.env` or expose API keys in source control.

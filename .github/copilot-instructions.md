# Workspace guidance

- Use Python 3.11+ and the local `.venv` for development.
- Keep the Streamlit resume-analysis workflow focused on PDF extraction, Groq calls, and clear validation errors.
- Store API keys in `.env`; never commit secrets.
- Validate changes with `python -m py_compile app.py` and the documented Streamlit command.

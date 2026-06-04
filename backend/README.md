# backend

FastAPI service that extracts text from an upload, runs a Gemini analysis pipeline, renders a PDF, and saves each run to PostgreSQL.

## Stack

Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL, Google Gemini (`google-genai`), PyMuPDF, fpdf2.

## Module map

| File | Responsibility |
| --- | --- |
| `api.py` | FastAPI app and HTTP endpoints. Runs extract, analyze, render, persist. |
| `extractor.py` | Pulls plain text out of `.pdf` (PyMuPDF) and `.txt` files. |
| `pipeline.py` | Sends text to Gemini 2.5 Flash, returns a structured `ContentAnalysis`. |
| `schemas.py` | Pydantic models for the analysis output (also used as Gemini's response schema). |
| `renderer.py` | Renders a `ContentAnalysis` to a PDF via fpdf2. |
| `models.py` | SQLAlchemy ORM models (the `jobs` table). |
| `db.py` | Engine, session factory, and the `get_db` request dependency. |
| `summarize.py` | CLI wrapper for running the pipeline without the server. |
| `alembic/` | Database migrations. |

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then fill in GEMINI_API_KEY and DATABASE_URL

alembic upgrade head              # requires a running Postgres

uvicorn api:app --reload --port 8000
```

### Environment variables

| Key | Example |
| --- | --- |
| `GEMINI_API_KEY` | `your-gemini-api-key-here` |
| `DATABASE_URL` | `postgresql://postgres:password@localhost:5432/summarizer` |

`.env` is gitignored. Copy `.env.example`, fill in real values, and do not commit `.env`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Heartbeat. |
| `POST` | `/analyze` | Send files or text (not both), returns `{ analysis, pdf_id }`. |
| `GET` | `/pdf/{id}` | Download the rendered PDF for a job. |
| `GET` | `/jobs` | 20 most recent jobs, newest first. |
| `GET` | `/jobs/{id}` | One full job, including its analysis. |

## CLI

Run the pipeline on a local file without starting the server:

```bash
python summarize.py sample_content.txt -o out.pdf
```

## Notes

- `output/` holds generated PDFs at runtime and is gitignored. The folder is kept via `.gitkeep`.
- Supported input types: `.pdf` (with a text layer) and `.txt`. Scanned or image-only PDFs are rejected, since OCR is not supported yet.
- Input is capped at 8,000 characters before being sent to Gemini, to limit API usage during development.

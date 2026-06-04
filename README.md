# CallToAction

> Read less. Act more.

A full-stack app that turns an article or document into an action-oriented summary. Instead of only telling you what the content said, it gives you things to do: key takeaways, action items, decisions to make, and open questions, plus a downloadable PDF.

The repo has two parts:

| Folder | What it is |
| --- | --- |
| `backend/` | Python FastAPI backend. Extracts text, runs a Gemini analysis pipeline, renders a PDF, and stores each run in Postgres. |
| `frontend/` | React 19 + TypeScript + Vite single-page app. Upload/paste UI, recent-jobs list, results view, PDF download. |

## How it works

```
Frontend (POST /analyze)
   -> extractor.py   (PDF/TXT to plain text via PyMuPDF)
   -> pipeline.py    (Gemini 2.5 Flash, structured JSON output)
   -> schemas.py     (Pydantic models enforce the output shape)
   -> renderer.py    (fpdf2 renders the analysis to a PDF)
   -> Postgres       (a Job row is saved: source, analysis JSONB, pdf path)
   -> response: { analysis, pdf_id }  ->  frontend renders + offers PDF download
```

The TypeScript types in `frontend/src/types/analysis.ts` mirror the Pydantic schemas in `backend/schemas.py`, so the API contract stays in sync.

## Backend (`backend/`)

Stack: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL, Google Gemini (`google-genai`), PyMuPDF, fpdf2.

### Setup

```bash
cd backend

# 1. Virtual env + deps
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Environment
cp .env.example .env
# then edit .env and set GEMINI_API_KEY and DATABASE_URL

# 3. Database (Postgres must be running)
alembic upgrade head

# 4. Run the API
uvicorn api:app --reload --port 8000
```

`.env` keys:

```
GEMINI_API_KEY=your-gemini-api-key-here
DATABASE_URL=postgresql://postgres:password@localhost:5432/summarizer
```

### Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Heartbeat |
| `POST` | `/analyze` | Upload files or text, returns analysis + `pdf_id` |
| `GET` | `/pdf/{id}` | Download the rendered PDF |
| `GET` | `/jobs` | 20 most recent jobs |
| `GET` | `/jobs/{id}` | One full job |

### CLI (no server needed)

```bash
python summarize.py sample_content.txt -o out.pdf
```

## Frontend (`frontend/`)

Stack: React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui (radix-nova).

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

The dev server expects the backend at `http://localhost:8000` (set in `src/lib/api/real.ts`). CORS on the backend is open to `localhost:5173`.

## Project status

Built in modules. Working today: text/PDF upload, Gemini analysis, PDF generation, job history. Planned next: WeasyPrint + Jinja2 templated rendering, image/OCR input, and object storage for PDFs.

## Notes

- Never commit `.env`. It holds your API key. Copy `.env.example` instead.
- `backend/output/` holds generated PDFs at runtime and is gitignored.
- No authentication yet. Intended for local, single-user development.

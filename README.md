# CallToAction

Turn a document, pasted text, or an image into a concise, action-oriented
summary and a downloadable PDF. CallToAction runs content through a staged
pipeline that compresses the source, extracts the key claims, and produces a
structured analysis: a one-line main point, key takeaways, and a call to action
with concrete next steps, decisions to make, and questions to explore.

The project has two parts:

- `backend/` is a FastAPI backend that runs the analysis pipeline,
  renders a PDF, and stores each run as a job in Postgres.
- `frontend/` is a React + Vite + TypeScript single-page app for uploading
  content and viewing results.

## How it works

The backend exposes an `/analyze` endpoint that accepts pasted text, a PDF or
text file, or an image. Input is routed through a pipeline:

1. Text and PDF input goes to Qwen 2.5 (served locally through llama-server),
   which compresses the source into a structured pack of claims and examples.
2. Image input first goes to MiniCPM-V (also via llama-server) for a text
   description, then follows the same Qwen path.
3. The compressed pack is sent to Google Gemini, which returns the final
   structured analysis.
4. The analysis is rendered to a PDF and saved, and a job record is written to
   the database.

A local `ModelManager` owns a single llama-server subprocess and swaps the
loaded model on demand, so the same GPU can serve both the text and vision
models without running them at once.

## Tech stack

**Backend** (`backend/`)

- Python, FastAPI, Uvicorn
- Pydantic for the structured output schema
- PyMuPDF for PDF text extraction
- Google GenAI SDK (Gemini) for the final analysis
- Local llama-server (Qwen 2.5, MiniCPM-V) for compression and vision
- SQLAlchemy and Alembic with PostgreSQL
- fpdf2 for PDF rendering

**Frontend** (`frontend/`)

- React, Vite, TypeScript
- Tailwind CSS and shadcn-style components
- Radix UI primitives, lucide-react icons

## API endpoints

| Method | Path            | Description                                      |
| ------ | --------------- | ------------------------------------------------ |
| GET    | `/health`       | Heartbeat                                        |
| POST   | `/analyze`      | Run the pipeline on text, a file, or an image    |
| GET    | `/pdf/{pdf_id}` | Download the rendered PDF for a job              |
| GET    | `/jobs`         | List the 20 most recent jobs                     |
| GET    | `/jobs/{job_id}`| Fetch one full job by ID                         |

## Getting started

### Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer
- PostgreSQL
- A Google Gemini API key
- Optional: a local llama-server build with the Qwen and MiniCPM-V models, for
  the text-compression and image stages

### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set GEMINI_API_KEY and DATABASE_URL

alembic upgrade head
uvicorn api:app --reload
```

The API starts on http://localhost:8000.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app starts on http://localhost:5173 and expects the API on port 8000.

## Configuration

The backend reads configuration from `backend/.env`. Use
`.env.example` as a template:

- `GEMINI_API_KEY` is required for the final analysis stage.
- `DATABASE_URL` is the PostgreSQL connection string.

The paths to the local llama-server executable and model files are set in
`backend/model_manager.py`. Adjust them to match your machine if you
want to run the Qwen and MiniCPM-V stages. If llama-server is not available, the
text stages will not run.

## Project status

This is a single-user, localhost project with no authentication. Some pieces
are scaffolding rather than finished features, including the local model server
wiring and automated tests. Treat it as a working prototype.

## License

Released under the MIT License. See [LICENSE](LICENSE).

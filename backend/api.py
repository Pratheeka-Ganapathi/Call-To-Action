"""
api.py — FastAPI server exposing the analysis pipeline over HTTP.

Routes:
  POST /analyze     — accept text/PDF or image, run pipeline, return analysis + pdf_id
  GET  /pdf/{id}    — return the PDF for a given pdf_id
  GET  /jobs        — return the 20 most recent jobs
  GET  /jobs/{id}   — return one full job by ID
  GET  /health      — heartbeat
"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from extractor import extract_text_from_bytes
from model_manager import manager
from models import Job
from pipeline import run_analysis, run_analysis_from_image
from renderer import render_to_pdf
from schemas import ContentAnalysis


load_dotenv()

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ────────── Lifecycle ──────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks. Cleanly stops llama-server when uvicorn exits."""
    yield
    print("Shutting down model manager...")
    manager.shutdown()


app = FastAPI(
    title="Content Summarizer API",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────── Response shapes ──────────


class AnalyzeResponse(BaseModel):
    analysis: ContentAnalysis
    pdf_id: str


class JobSummary(BaseModel):
    """Lightweight job info for list views."""
    id: str
    created_at: str
    source_kind: str
    source_label: str

    model_config = {"from_attributes": True}


class JobDetail(BaseModel):
    """Full job for detail view."""
    id: str
    created_at: str
    source_kind: str
    source_label: str
    analysis: ContentAnalysis

    model_config = {"from_attributes": True}


# ────────── Helpers ──────────


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _file_extension(filename: Optional[str]) -> str:
    """Return the lowercase extension including the dot, or empty string."""
    if not filename or "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


# ────────── Endpoints ──────────


@app.get("/health")
def health() -> dict:
    """Heartbeat. Used by the frontend to confirm the server is reachable."""
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    files: list[UploadFile] = File(default=[]),
    text: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    """Run the analysis pipeline, save the PDF, persist a Job row.

    Routes:
      - Image files (PNG/JPG/JPEG/WEBP/GIF) → image pipeline (MiniCPM → Qwen → Gemini)
      - PDF/TXT files → text pipeline (Qwen → Gemini)
      - Pasted text → text pipeline
    """
    has_files = len(files) > 0 and any(f.filename for f in files)
    has_text = text is not None and text.strip() != ""

    if not has_files and not has_text:
        raise HTTPException(400, "Provide either files or text.")
    if has_files and has_text:
        raise HTTPException(400, "Provide files OR text, not both.")

    # Decide which pipeline to use, run it, and capture source metadata.
    try:
        if has_files:
            first = files[0]
            first_ext = _file_extension(first.filename)

            if first_ext in IMAGE_EXTENSIONS:
                # Image pipeline. Only one image at a time.
                if len(files) > 1:
                    raise HTTPException(
                        400, "Only one image at a time is supported."
                    )
                image_bytes = await first.read()
                analysis = run_analysis_from_image(
                    image_bytes, first.filename or "image"
                )
                source_kind = "image"
                source_label = first.filename or "image"
            else:
                # Text/PDF pipeline. Concatenate all files.
                parts = []
                for upload in files:
                    data = await upload.read()
                    parts.append(
                        extract_text_from_bytes(upload.filename or "file", data)
                    )
                content = "\n\n".join(parts)
                analysis = run_analysis(content)
                source_kind = "file"
                source_label = ", ".join(
                    [(f.filename or "unnamed") for f in files]
                )[:500]
        else:
            # Pasted text pipeline.
            analysis = run_analysis(text or "")
            source_kind = "text"
            source_label = (text or "")[:100]
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        # Re-raise — these are intentional 4xx errors (like the multi-image guard).
        raise
    except Exception as e:
        raise HTTPException(502, f"Analysis failed: {e}")

    # Render PDF and assign an ID.
    pdf_id = uuid.uuid4()
    pdf_path = OUTPUT_DIR / f"{pdf_id}.pdf"
    render_to_pdf(analysis, pdf_path)

    # Persist a Job row.
    job = Job(
        id=pdf_id,
        source_kind=source_kind,
        source_label=source_label,
        analysis=analysis.model_dump(),
        pdf_path=str(pdf_path),
    )
    db.add(job)
    db.commit()

    return AnalyzeResponse(analysis=analysis, pdf_id=str(pdf_id))


@app.get("/pdf/{pdf_id}")
def get_pdf(pdf_id: str, db: Session = Depends(get_db)) -> FileResponse:
    """Return the PDF for a given pdf_id, looked up via the database."""
    try:
        job_uuid = uuid.UUID(pdf_id)
    except ValueError:
        raise HTTPException(400, "Invalid pdf_id format.")

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if job is None:
        raise HTTPException(404, "Job not found.")

    pdf_path = Path(job.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(410, "PDF file no longer exists on disk.")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"summary-{pdf_id[:8]}.pdf",
    )


@app.get("/jobs", response_model=list[JobSummary])
def list_jobs(db: Session = Depends(get_db)) -> list[JobSummary]:
    """Return the 20 most recent jobs, newest first."""
    jobs = (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        JobSummary(
            id=str(job.id),
            created_at=job.created_at.isoformat(),
            source_kind=job.source_kind,
            source_label=job.source_label,
        )
        for job in jobs
    ]


@app.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobDetail:
    """Return one full job by ID."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(400, "Invalid job_id format.")

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if job is None:
        raise HTTPException(404, "Job not found.")

    return JobDetail(
        id=str(job.id),
        created_at=job.created_at.isoformat(),
        source_kind=job.source_kind,
        source_label=job.source_label,
        analysis=job.analysis,
    )
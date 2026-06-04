"""
api.py — FastAPI server exposing the analysis pipeline over HTTP.

Now wired to PostgreSQL via SQLAlchemy. Each /analyze call writes a Job row.
"""

import uuid
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
from models import Job
from pipeline import run_analysis
from renderer import render_to_pdf
from schemas import ContentAnalysis


load_dotenv()

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


app = FastAPI(title="CallToAction API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ───── Response shapes ─────


class AnalyzeResponse(BaseModel):
    analysis: ContentAnalysis
    pdf_id: str

class JobSummary(BaseModel):
    """Lightweight job info for list views."""
    id: str
    created_at: str
    source_kind: str
    source_label: str

    # Tells Pydantic it's allowed to read attributes from ORM objects,
    # not just dicts. Otherwise it'd complain that Job isn't a dict.
    model_config = {"from_attributes": True}


class JobDetail(BaseModel):
    """Full job for detail view — same as JobSummary plus the analysis."""
    id: str
    created_at: str
    source_kind: str
    source_label: str
    analysis: ContentAnalysis

    model_config = {"from_attributes": True}
# ───── Helpers ─────


def _build_source_label(
    files: list[UploadFile], text: Optional[str]
) -> tuple[str, str]:
    """Return (source_kind, source_label) for the Job row.

    For files: comma-joined filenames, truncated to 500 chars.
    For text: first 100 chars of the pasted content.
    """
    has_files = len(files) > 0 and any(f.filename for f in files)
    if has_files:
        names = [f.filename or "unnamed" for f in files]
        label = ", ".join(names)[:500]
        return "file", label
    label = (text or "")[:100]
    return "text", label


# ───── Endpoints ─────


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
    """Run the analysis pipeline, save the PDF, and persist a Job row."""
    # Validate input.
    has_files = len(files) > 0 and any(f.filename for f in files)
    has_text = text is not None and text.strip() != ""

    if not has_files and not has_text:
        raise HTTPException(400, "Provide either files or text.")
    if has_files and has_text:
        raise HTTPException(400, "Provide files OR text, not both.")

    # Extract content.
    try:
        if has_files:
            parts = []
            for upload in files:
                data = await upload.read()
                parts.append(
                    extract_text_from_bytes(upload.filename or "file", data)
                )
            content = "\n\n".join(parts)
        else:
            content = text or ""
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Run pipeline.
    try:
        analysis = run_analysis(content)
    except Exception as e:
        raise HTTPException(502, f"Analysis failed: {e}")

    # Render PDF.
    pdf_id = uuid.uuid4()
    pdf_path = OUTPUT_DIR / f"{pdf_id}.pdf"
    render_to_pdf(analysis, pdf_path)

    # Persist a Job row.
    source_kind, source_label = _build_source_label(files, text)
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

    # Look up the job in the database.
    # If it doesn't exist, the PDF doesn't either (regardless of disk state).
    job = db.query(Job).filter(Job.id == job_uuid).first()
    if job is None:
        raise HTTPException(404, "Job not found.")

    pdf_path = Path(job.pdf_path)
    if not pdf_path.exists():
        # The DB has a record but the file is missing — disk and DB out of sync.
        # 410 Gone is more accurate than 404 here.
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
"""
models.py — SQLAlchemy ORM models.

Each class here corresponds to one database table. Adding a column means
adding an attribute and running a new Alembic migration.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Job(Base):
    """One analysis run — what the user uploaded plus what came back."""
    __tablename__ = "jobs"

    # Primary key. We generate UUIDs in Python instead of letting Postgres
    # do it, so we can return the ID to the user before commit if needed.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # When the analysis was created. timezone-aware UTC.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # "file" or "text" — what kind of input the user provided.
    source_kind: Mapped[str] = mapped_column(String(16), nullable=False)

    # Filename(s) joined with commas, OR first 100 chars of pasted text.
    # Used to label the job in a history list later.
    source_label: Mapped[str] = mapped_column(String(500), nullable=False)

    # The full ContentAnalysis serialized as JSON.
    # JSONB is Postgres's binary JSON — fast to query and index.
    analysis: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Path to the rendered PDF on disk. Local filesystem for now;
    # becomes an object storage key in Module E.
    pdf_path: Mapped[str] = mapped_column(String(500), nullable=False)
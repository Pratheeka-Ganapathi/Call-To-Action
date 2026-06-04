"""
db.py — SQLAlchemy engine and session setup.

The engine is the connection pool. One per process, created at startup.
A Session is one unit of work (one HTTP request, typically). Sessions are
cheap to create and short-lived.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. Check your .env file.")


# Engine = connection pool. SQLAlchemy reuses connections across sessions
# automatically, so we just create one engine for the whole app.
# echo=False keeps logs quiet; flip to True if you want to see every SQL query.
engine = create_engine(DATABASE_URL, echo=False)


# SessionLocal is a factory: SessionLocal() gives us a fresh Session.
# We'll use this in api.py to get a Session per request.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models.

    Every model class in models.py inherits from Base. SQLAlchemy uses this
    inheritance to discover tables and generate schema.
    """
    pass

def get_db():
    """FastAPI dependency that yields a database session per request.

    The yield pattern means: open a session, give it to the endpoint, then
    after the endpoint returns (success or exception), close the session.

    Used as: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
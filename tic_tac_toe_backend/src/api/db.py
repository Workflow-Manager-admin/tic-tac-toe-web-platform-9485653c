import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL not set in environment (.env) file.")

engine = create_engine(DATABASE_URL, poolclass=NullPool)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

# PUBLIC_INTERFACE
def get_db():
    """Get a new DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

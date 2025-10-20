from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

# SQLite - creates local db.sqlite3 file
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Check for env variable existence
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL not configured in .env file")

# For SQLite only checking thread.
#engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

#For MySQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# get database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
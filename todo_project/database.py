import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@0.0.0.0:5432/{os.getenv('POSTGRES_DB')}"
)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    # SELECT application_name, query FROM pg_stat_activity
    connect_args={"application_name": "FastAPI_1"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

try:
    db = SessionLocal()
    db.execute(text("SELECT 1"))
except Exception as e:
    raise e
finally:
    db.close()


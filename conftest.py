import os
import pytest
import sys
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from todo_project.database import Base, SessionLocal, engine
from todo_project.dependencies import get_db
from todo_project.main import app


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Override database URL for tests
SQLALCHEMY_DATABASE_URL_TEST = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@0.0.0.0/testing"
)

# Create all tables for test database
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a clean database session for each test function.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session):
    # Override the `get_db` dependency to use the `db_session` fixture
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client

    # Clean up after test
    app.dependency_overrides.clear()

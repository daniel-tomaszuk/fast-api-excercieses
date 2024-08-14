import logging
import os
import pytest
import sys

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from todo_project.dependencies import get_db
from todo_project.main import app
from todo_project.models import Users
from todo_project.routers.auth import get_current_user

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


# Override database URL for tests
SQLALCHEMY_DATABASE_URL_TEST = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@0.0.0.0/testing"
)
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    pool_pre_ping=True,
    # useful for SELECT application_name, query FROM pg_stat_activity
    connect_args={"application_name": "Pytest_1"}
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create all tables for test database
Base = declarative_base()
Base.metadata.create_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a clean database session for each test function.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    test_session = TestSession(bind=connection)
    try:
        yield test_session
    finally:
        transaction.rollback()  # Roll back the outer transaction
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


@pytest.fixture(scope="function")
def regular_user(db_session) -> dict:
    """
    Gets or creates regular (non admin) user from the DB.
    Overrides 'user_dependency' for the time being of test.
    """

    def override_user_dependency():
        regular_user_username = "pytest_test_user_1"
        regular_test_user = db_session.query(Users).filter(Users.username == regular_user_username).first()
        if regular_test_user:
            return dict(
                username=regular_test_user.username,
                id=regular_test_user.id,
                role=regular_test_user.role,
            )

        regular_test_user = Users(
            username=regular_user_username,
            email="test_user_1@pytest.com",
            first_name=f"Test First Name",
            last_name=f"Test Last Name",
            is_active=True,
            role="user",
            phone_number="123456789",
        )
        db_session.add(regular_test_user)
        db_session.commit()
        return dict(username=regular_test_user.username, id=regular_test_user.id, role=regular_test_user.role)

    app.dependency_overrides[get_current_user] = override_user_dependency

    try:
        yield override_user_dependency()
    finally:
        # Clean up after test
        app.dependency_overrides.clear()

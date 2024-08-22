Example config for FastAPI, pytest, PostgreSQL in Docker.

DB and user dependencies are mocked for every test, there is a DB transaction rollback after each test.
SQLAlchemy with Alembic is used as a ORM / DB management tools.

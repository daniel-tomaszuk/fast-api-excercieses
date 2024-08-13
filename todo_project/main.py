from todo_project import models
from todo_project.database import engine
from todo_project.routers import admin, auth, todos, users

from fastapi import FastAPI


app = FastAPI()
models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(todos.router)

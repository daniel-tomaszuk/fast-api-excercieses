from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Path
from fastapi import status

from todo_project.dependencies import db_dependency
from todo_project.routers.auth import user_dependency
from todo_project.serializers.serializers import TodoRequest
from todo_project.models import Todos

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    return db.query(Todos).filter(Todos.owner_id == user["id"]).all()


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(ge=0)):
    todo_model = db.query(Todos).filter(Todos.owner_id == user["id"], Todos.id == todo_id).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    todo_model = Todos(**todo_request.model_dump(), owner_id=user["id"])
    db.add(todo_model)
    db.commit()
    return todo_model


@router.put("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(ge=0)):
    todo_model = db.query(Todos).filter(Todos.owner_id == user["id"], Todos.id == todo_id).first()
    if not todo_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()

    return todo_model

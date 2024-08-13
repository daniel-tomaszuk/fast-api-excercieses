from fastapi import APIRouter
from fastapi import status, HTTPException
from fastapi import Path

from todo_project.dependencies import db_dependency
from todo_project.models import Todos
from todo_project.routers.auth import user_dependency


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    return db.query(Todos).all()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(ge=0)):
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    object_exists: int = db.query(Todos).filter(Todos.id == todo_id).count()
    if object_exists == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()

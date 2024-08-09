import bcrypt
from fastapi import APIRouter
from fastapi import status

from todo_project.dependencies import db_dependency
from todo_project.models import Users
from todo_project.serializers.serializers import CreateUserRequest

router = APIRouter()


@router.post("/auth/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    hashed: bytes = bcrypt.hashpw(str(create_user_request.password).encode("UTF-8"), bcrypt.gensalt())
    hashed: str = hashed.decode("UTF-8")
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=hashed,
        is_active=True,
    )
    db.add(create_user_model)
    db.commit()

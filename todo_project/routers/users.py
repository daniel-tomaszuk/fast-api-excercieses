import bcrypt
from fastapi import APIRouter
from fastapi import status, HTTPException

from todo_project.dependencies import db_dependency
from todo_project.models import Users
from todo_project.routers.auth import user_dependency
from todo_project.serializers.serializers import User, ResetPasswordRequest, UpdateUserRequest

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user(user: user_dependency, db: db_dependency) -> User:
    user = db.query(Users).filter(Users.id == user["id"]).first()
    return User(
        id=user.id,
        username=user.username,
        is_active=user.is_active,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        phone_number=user.phone_number,
    )


@router.put("/me", status_code=status.HTTP_200_OK)
async def update_current_user(user: user_dependency, db: db_dependency, payload: UpdateUserRequest) -> User:
    user = db.query(Users).filter(Users.id == user["id"]).first()

    if payload.first_name is not None:
        user.first_name = payload.first_name

    if payload.last_name is not None:
        user.last_name = payload.last_name

    if payload.email is not None:
        user.email = payload.email

    if payload.phone_number is not None:
        user.phone_number = payload.phone_number

    db.commit()
    return user


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_user_password(user: user_dependency, db: db_dependency, payload: ResetPasswordRequest):
    user = db.query(Users).filter(Users.id == user["id"]).first()
    old_password: str = payload.old_password
    is_valid: bool = bcrypt.checkpw(str(old_password).encode("UTF-8"), str(user.hashed_password).encode("UTF-8"))
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    new_password = payload.new_password
    hashed: bytes = bcrypt.hashpw(str(new_password).encode("UTF-8"), bcrypt.gensalt())
    hashed: str = hashed.decode("UTF-8")

    user.hashed_password = hashed
    db.commit()

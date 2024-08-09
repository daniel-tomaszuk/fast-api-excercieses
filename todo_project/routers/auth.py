import datetime
import os
from datetime import timedelta
from typing import Annotated

import bcrypt

from authlib.jose import jwt
from fastapi import APIRouter
from fastapi import status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from todo_project.dependencies import db_dependency
from todo_project.models import Users
from todo_project.serializers.serializers import CreateUserRequest, Token

router = APIRouter()

# openssl rand -hex 32
JWT_SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALG = "HS512"


async def authenticate_user(db: db_dependency, username: str, password: str) -> Users | None:
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return None

    is_valid: bool = bcrypt.checkpw(str(password).encode("UTF-8"), str(user.hashed_password).encode("UTF-8"))
    if not is_valid:
        return None

    return user


async def create_access_token(username: str, user_id: int, expires_delta: timedelta) -> str:
    payload = dict(
        sub=username,
        id=user_id,
        exp=datetime.datetime.now(datetime.timezone.utc) + expires_delta
    )
    header = dict(alg=JWT_ALG)
    return jwt.encode(header=header, payload=payload, key=JWT_SECRET_KEY).decode("UTF-8")


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


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency,
):
    user: Users | None = await authenticate_user(
        db,
        username=form_data.username,
        password=form_data.password,
    )
    if user:
        token: str = await create_access_token(
            username=user.username,
            user_id=user.id,
            expires_delta=timedelta(minutes=10),
        )
        return dict(access_token=token, token_type="Bearer")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")

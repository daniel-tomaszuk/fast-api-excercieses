from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field


class UserRoleEnumerate(StrEnum):
    admin = "admin"
    user = "user"


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str | None = Field(max_length=100)
    priority: int = Field(ge=0, le=5)
    complete: bool = False


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: UserRoleEnumerate = UserRoleEnumerate.user


class ResetPasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    id: int
    username: str
    is_active: bool
    first_name: str
    last_name: str
    email: str
    role: UserRoleEnumerate = UserRoleEnumerate.user

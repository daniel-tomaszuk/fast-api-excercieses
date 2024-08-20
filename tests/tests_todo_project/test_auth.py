import datetime
from datetime import timedelta

import pytest
import time_machine
from authlib.jose import jwt

import todo_project.routers.auth as auth_module
from todo_project.routers.auth import authenticate_user, create_access_token


class TestAuth:
    @pytest.mark.asyncio
    async def test_authenticate_user(self, db_session, regular_user):
        user = await authenticate_user(
            db=db_session,
            username=regular_user["username"],
            password="test-12345",
        )
        assert user is not None
        assert user.id == regular_user["id"]
        assert user.username == regular_user["username"]
        assert user.role == regular_user["role"]

    @pytest.mark.asyncio
    async def test_authenticate_user__invalid_password(self, db_session, regular_user):
        user = await authenticate_user(
            db=db_session,
            username=regular_user["username"],
            password="invalid-password",
        )
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user__invalid_username(self, db_session, regular_user):
        user = await authenticate_user(
            db=db_session,
            username="invalid-username",
            password="test-12345",
        )
        assert user is None

    @pytest.mark.asyncio
    @time_machine.travel("2024-06-01", tick=False)
    async def test_create_access_token(self, monkeypatch):
        input_token_payload = dict(
            username="test-username",
            user_id=12345,
            role="test-role",
            expires_delta=timedelta(hours=2)
        )

        monkeypatch.setattr(auth_module, "JWT_SECRET_KEY", "test-jwt-secret")
        token: str = await create_access_token(
            **input_token_payload
        )
        assert token is not None

        token_payload: "JWTClaims" = jwt.decode(token, "test-jwt-secret")
        assert token_payload["exp"] == (
            (
                datetime.datetime.now(datetime.timezone.utc)
                + input_token_payload["expires_delta"]
            ).timestamp()
        )
        assert token_payload["id"] == input_token_payload["user_id"]
        assert token_payload["role"] == input_token_payload["role"]
        assert token_payload["sub"] == input_token_payload["username"]

        assert token_payload.header == dict(alg=auth_module.JWT_ALG, typ="JWT")

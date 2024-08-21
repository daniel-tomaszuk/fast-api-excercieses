import datetime
from datetime import timedelta
from typing import Coroutine

import pytest
import time_machine
from authlib.jose import jwt
from fastapi import HTTPException
from fastapi import status

import todo_project.routers.auth as auth_module
from todo_project.routers.auth import authenticate_user, create_access_token, get_current_user


@pytest.fixture()
def jwt_token_user_info() -> dict:
    return dict(
        username="test-username",
        user_id=12345,
        role="test-role",
        expires_delta=timedelta(hours=2)
    )


@pytest.mark.asyncio
@time_machine.travel("2024-06-01", tick=False)
@pytest.fixture()
async def jwt_token(monkeypatch, jwt_token_user_info: dict) -> str:
    monkeypatch.setattr(auth_module, "JWT_SECRET_KEY", "test-jwt-secret")
    token: str = await create_access_token(**jwt_token_user_info)
    return token


@pytest.mark.asyncio
@time_machine.travel("2024-06-01", tick=False)
@pytest.fixture()
async def jwt_invalid_token(monkeypatch, jwt_token_user_info: dict) -> str:
    monkeypatch.setattr(auth_module, "JWT_SECRET_KEY", "test-jwt-secret")
    invalid_jwt_token_user_info = jwt_token_user_info
    invalid_jwt_token_user_info["username"] = ""
    invalid_jwt_token_user_info["user_id"] = ""
    token: str = await create_access_token(**jwt_token_user_info)
    return token


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

    @pytest.mark.asyncio
    @time_machine.travel("2024-06-01", tick=False)
    async def test_get_current_user(self, jwt_token: Coroutine, jwt_token_user_info: dict):
        user_info: dict = await get_current_user(await jwt_token)

        assert user_info
        assert user_info["id"] == jwt_token_user_info["user_id"]
        assert user_info["role"] == jwt_token_user_info["role"]
        assert user_info["username"] == jwt_token_user_info["username"]

    @pytest.mark.asyncio
    @time_machine.travel("2024-06-01", tick=False)
    async def test_get_current_user__token_expired(self, jwt_token: Coroutine):
        # Given valid token is present
        jwt_token: str = await jwt_token

        # When valid token is used after it expires
        with time_machine.travel("2024-06-02"):
            with pytest.raises(HTTPException) as e:
                await get_current_user(jwt_token)

        # Then we expect proper unauthorized error to raise
        assert e.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert e.value.detail == "Could not validate credentials."

    @pytest.mark.asyncio
    @time_machine.travel("2024-06-01", tick=False)
    async def test_get_current_user__token_decoding_error(self, jwt_token: Coroutine):
        # Given valid token is present
        jwt_token: str = await jwt_token

        # When token is manually modified
        jwt_token = jwt_token[0:len(jwt_token) - 1]

        # Then we expect proper unauthorized exception to rise
        with pytest.raises(HTTPException) as e:
            await get_current_user(jwt_token)

        assert e.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert e.value.detail == "Could not validate credentials."

    @pytest.mark.asyncio
    @time_machine.travel("2024-06-01", tick=False)
    async def test_get_current_user__token_missing_user_info(self, jwt_invalid_token: Coroutine, jwt_token_user_info: dict):
        jwt_token: str = await jwt_invalid_token

        # When token is used to get the user
        with pytest.raises(HTTPException) as e:
            await get_current_user(jwt_token)

        # Then we expect proper unauthorized exception to rise
        assert e.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert e.value.detail == "Could not validate credentials."

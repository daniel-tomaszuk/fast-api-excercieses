import datetime
import json
from datetime import timedelta
from typing import Coroutine

import bcrypt
import pytest
import time_machine
from authlib.jose import jwt
from fastapi import HTTPException
from fastapi import status

import todo_project.routers.auth as auth_module
from todo_project.models import Users
from todo_project.routers.auth import JWT_TOKEN_LIFETIME_SECONDS, authenticate_user, create_access_token, get_current_user


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


@pytest.fixture()
def create_user_payload():
    return {
        "username": "test-new-user-1",
        "email": "test-new-user-email-1@example.com",
        "first_name": "first-name",
        "last_name": "last-name",
        "password": "test-password-12345",
        "role": "user",
        "phone_number": "123-123456789",
    }


@pytest.fixture()
def login_for_access_token_payload(regular_user: dict):
    return dict(username=regular_user["username"], password="test-12345")


class TestAuth:
    BASE_URL = "/auth"

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

    def test_create_user(self, client, db_session, create_user_payload):
        response = client.post(self.BASE_URL + "/create-user", data=json.dumps(create_user_payload))
        assert response.status_code == status.HTTP_201_CREATED

        new_user = db_session.query(Users).filter(Users.username == create_user_payload["username"]).first()
        assert new_user
        assert new_user.email == create_user_payload["email"]
        assert new_user.first_name == create_user_payload["first_name"]
        assert new_user.last_name == create_user_payload["last_name"]
        assert new_user.role == create_user_payload["role"]
        assert new_user.is_active is True
        assert new_user.phone_number == create_user_payload["phone_number"]

        is_valid: bool = bcrypt.checkpw(
            str(create_user_payload["password"]).encode("UTF-8"),
            str(new_user.hashed_password).encode("UTF-8")
        )
        assert is_valid is True

    @pytest.mark.parametrize(
        "missing_key", [
            "username", "email", "first_name", "last_name", "password",
        ]
    )
    def test_create_user__missing_data(self, client, db_session, create_user_payload, missing_key):
        del create_user_payload[missing_key]
        response = client.post(self.BASE_URL + "/create-user", data=json.dumps(create_user_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user__invalid_role(self, client, db_session, create_user_payload):
        create_user_payload["role"] = "invalid-test-role"
        response = client.post(self.BASE_URL + "/create-user", data=json.dumps(create_user_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_for_access_token(self, monkeypatch, client, login_for_access_token_payload: dict):
        monkeypatch.setattr(auth_module, "JWT_SECRET_KEY", "test-jwt-secret")

        response = client.post(
            self.BASE_URL + "/token",
            data=login_for_access_token_payload,
            headers=dict(
                accept="application/json",
                content_type="application/x-www-form-urlencoded",
            )
        )
        assert response.status_code == status.HTTP_200_OK

        payload = response.json()
        assert "access_token" in payload
        assert "token_type" in payload
        assert "expires_in" in payload
        assert payload["token_type"] == "Bearer"
        assert payload["expires_in"] == JWT_TOKEN_LIFETIME_SECONDS

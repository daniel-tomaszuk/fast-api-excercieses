import json

import bcrypt
import pytest
from fastapi import status

from todo_project.models import Users


class TestUsersAPI:
    BASE_URL = "/users"

    def test_get_current_user_info(self, client, regular_user):
        response = client.get(self.BASE_URL + "/me")
        assert response.status_code == status.HTTP_200_OK

        payload: dict = response.json()
        assert all(
            key in payload
            for key in
            ("id", "username", "is_active", "first_name", "last_name", "email", "role", "phone_number")
        )
        assert payload["id"] == regular_user["id"]
        assert payload["username"] == regular_user["username"]
        assert payload["role"] == regular_user["role"]
        assert "hashed_password" not in payload

    @pytest.mark.parametrize(
        "attribute_name, value",
        [
            ("first_name", "New First Name"),
            ("last_name", "New Last Name"),
            ("email", "new_email_12345@example.com"),
            ("phone_number", "123321123321"),
        ]
                             )
    def test_update_current_user_info__basic_info_success(self, client, db_session, regular_user, attribute_name, value):
        response = client.put(self.BASE_URL + "/me", data=json.dumps({attribute_name: value}))
        assert response.status_code == status.HTTP_200_OK

        payload = response.json()
        assert payload.get(attribute_name) == value

        updated_user = db_session.query(Users).filter(Users.id == regular_user["id"]).first()
        assert getattr(updated_user, attribute_name, None) == value

    def test_reset_user_password(self, client, db_session, regular_user):
        response = client.post(self.BASE_URL + "/reset-password", data=json.dumps(
            {"old_password": "test-12345", "new_password": "test-54321"}
        ))
        assert response.status_code == status.HTTP_204_NO_CONTENT

        updated_user = db_session.query(Users).filter(Users.id == regular_user["id"]).first()
        assert bcrypt.checkpw(
            str("test-54321").encode("UTF-8"),
            str(updated_user.hashed_password).encode("UTF-8"),
        )

    def test_reset_user_password__invalid_old_password(self, client, db_session, regular_user):
        response = client.post(self.BASE_URL + "/reset-password", data=json.dumps(
            {"old_password": "invalid-old-password", "new_password": "test-54321"}
        ))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

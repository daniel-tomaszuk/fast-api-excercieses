import json
import typing as t

from conftest import TestSession
from todo_project.models import Todos

import pytest
from fastapi import status


@pytest.fixture
def default_todos(regular_user) -> list[dict[str, t.Any]]:
    return [
        {
            "title": f"Title {i}",
            "description": f"Description {i}",
            "priority": i % 5,
            "complete": True if i % 2 == 1 else False,
            "owner_id": regular_user["id"],
        } for i in range(10)
    ]


@pytest.fixture
def default_post_payload() -> dict:
    return {
        "title": "Correct POST payload",
        "description": "Used for POST request testing",
        "priority": 5,
        "complete": True,
    }


@pytest.fixture
def load_fixtures(db_session, default_todos):
    for todo in default_todos:
        todo_model = Todos(**todo)
        db_session.add(todo_model)
    db_session.commit()


class TestTodos:

    def test_read_all(self, client, load_fixtures, default_todos):
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        default_todos = [
            {key: value for key, value in todo.items() if key != "id"} for todo in default_todos
        ]
        response = [
            {key: value for key, value in row.items() if key != "id"} for row in response.json()
        ]
        assert response == default_todos

    def test_get_one_item_by_id(self, client, db_session, load_fixtures, default_todos):
        existing_todo_id = db_session.query(Todos).first().id
        response = client.get(f"/todo/{existing_todo_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            **default_todos[0],
            "id": existing_todo_id,
        }

    @pytest.mark.parametrize("invalid_id", [
        -1, 5.25, "abcd", None, ";DROP DB;"
    ])
    def test_get_one_item_by_id__invalid_id(self, client, load_fixtures, invalid_id):
        response = client.get(f"/todo/{invalid_id}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_one_item_by_id__not_found(self, client, load_fixtures, default_todos):
        response = client.get(f"/todo/{len(default_todos) + 1}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_one_item(self, client, load_fixtures, default_post_payload):
        response = client.post("/todo", data=json.dumps(default_post_payload))
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_one_item__title_too_short(self, client, load_fixtures, default_post_payload):
        invalid_payload = default_post_payload
        invalid_payload["title"] = "a" * 2
        response = client.post("/todo", data=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_one_item__description_too_long(self, client, load_fixtures, default_post_payload):
        invalid_payload = default_post_payload
        invalid_payload["description"] = "a" * 101
        response = client.post("/todo", data=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize("invalid_priority", [-1, 6, "abcd", "", None])
    def test_create_one_item__invalid_priority(self, client, load_fixtures, default_post_payload, invalid_priority):
        invalid_payload = default_post_payload
        invalid_payload["priority"] = invalid_priority
        response = client.post("/todo", data=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize("invalid_complete_flag", [-1, 6, "abcd", "", None])
    def test_create_one_item__invalid_priority(self, client, load_fixtures, default_post_payload, invalid_complete_flag):
        invalid_payload = default_post_payload
        invalid_payload["complete"] = invalid_complete_flag
        response = client.post("/todo", data=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_one_item(self, client, db_session, load_fixtures, default_post_payload):
        existing_todo_id = db_session.query(Todos).first().id
        response = client.put(f"/todo/{existing_todo_id}", data=json.dumps(default_post_payload))
        assert response.status_code == status.HTTP_200_OK

    def test_update_one_item__not_found(self, client, load_fixtures, default_post_payload):
        response = client.put("/todo/20", data=json.dumps(default_post_payload))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_one_item__title_too_short(self, client, load_fixtures, default_post_payload):
        invalid_payload = default_post_payload
        invalid_payload["title"] = "a" * 2
        response = client.put("/todo/1", data=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_one_item__description_too_long(self, client, load_fixtures, default_post_payload):
        invalid_payload = default_post_payload
        invalid_payload["description"] = "a" * 101
        response = client.put("/todo/1", data=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize("invalid_priority", [-1, 6, "abcd", "", None])
    def test_update_one_item__invalid_priority(self, client, load_fixtures, default_post_payload, invalid_priority):
        invalid_payload = default_post_payload
        invalid_payload["priority"] = invalid_priority
        response = client.put("/todo/1", data=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize("invalid_complete_flag", [-1, 6, "abcd", "", None])
    def test_update_one_item__invalid_priority(self, client, load_fixtures, default_post_payload, invalid_complete_flag):
        invalid_payload = default_post_payload
        invalid_payload["complete"] = invalid_complete_flag
        response = client.put("/todo/1", data=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

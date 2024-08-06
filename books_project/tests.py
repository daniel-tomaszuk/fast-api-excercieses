import json

from books_project.books import app

import pytest
from fastapi.testclient import TestClient
from starlette import status

client = TestClient(app)


class TestBooksAPI:

    def test_get_all_books(self):
        response = client.get("/books-all/")
        assert response.status_code == status.HTTP_200_OK
        
        resp_json = response.json()
        assert resp_json and len(resp_json) == 10
        assert all(row.get("author") is not None for row in resp_json)
        assert all(row.get("id") is not None for row in resp_json)
        assert all(row.get("description") is not None for row in resp_json)
        assert all(row.get("rating") is not None for row in resp_json)
        assert all(row.get("title") is not None for row in resp_json)

    @pytest.mark.parametrize(
        "valid_id", [0, 1, 2, 9]
    )
    def test_get_book_by_id(self, valid_id):
        response = client.get(f"/books/{valid_id}")
        assert response.status_code == status.HTTP_200_OK

        resp_json = response.json()
        assert "id" in resp_json
        assert "author" in resp_json
        assert "description" in resp_json
        assert "rating" in resp_json
        assert "title" in resp_json
        assert resp_json["id"] == valid_id

    def test_get_book_by_id__not_found(self):
        response = client.get("/books/99")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "invalid_id", [
            "abc", None, -1, 3.14, [], {}, (), ";DROP DB;"
        ]
    )
    def test_get_book_by_id__invalid_id(self, invalid_id):
        response = client.get(f"/books/{invalid_id}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        "valid_rating", [0, 10]
    )
    def test_get_book_by_rating(self, valid_rating):
        response = client.get(f"/books-by-rating?book_rating={valid_rating}")
        assert response.status_code == status.HTTP_200_OK
        assert all(book.get("rating") == valid_rating for book in response.json())

    @pytest.mark.parametrize(
        "invalid_rating", [-1, 11, "abcd", None, ";DROP DB;"]
    )
    def test_get_book_by_rating__invalid_query_param(self, invalid_rating):
        response = client.get(f"/books-by-rating?book_rating={invalid_rating}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_new_book(self):
        test_payload = {
            "title": "Test title",
            "author": "Test author",
            "description": "Test description",
            "rating": 8,
        }
        response = client.post("/books/add", content=json.dumps(test_payload))
        assert response.status_code == status.HTTP_201_CREATED

        new_book_id = response.json().get("id")
        response = client.get(f"/books/{new_book_id}")
        assert response.status_code == status.HTTP_200_OK

        resp_json = response.json()
        assert resp_json["id"] == new_book_id
        assert resp_json["title"] == "Test title"
        assert resp_json["author"] == "Test author"
        assert resp_json["description"] == "Test description"
        assert resp_json["rating"] == 8

    @pytest.mark.parametrize(
        "invalid_payload", [
            {
                "title": 1234,
                "author": "Test author",
                "description": "Test description",
                "rating": 8,
            },
            {
                "title": "Test",
                "description": "Test description",
                "rating": 8,
            },
            {
                "author": "Test author",
                "description": "Test description",
                "rating": 3,
            },
            {},
        ]
    )
    def test_create_new_book__invalid_payload(self, invalid_payload):
        response = client.post("/books/add", content=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_a_book(self):
        test_payload = {
            "title": "Test title",
            "author": "Test author",
            "description": "Test description",
            "rating": 8,
        }
        response = client.put("/books/update/3", content=json.dumps(test_payload))
        assert response.status_code == status.HTTP_200_OK

        response = client.get(f"/books/3")
        assert response.status_code == status.HTTP_200_OK

        resp_json = response.json()
        assert resp_json["id"] == 3
        assert resp_json["title"] == "Test title"
        assert resp_json["author"] == "Test author"
        assert resp_json["description"] == "Test description"
        assert resp_json["rating"] == 8

    @pytest.mark.parametrize(
        "invalid_payload", [
            {
                "title": 1234,
                "author": "Test author",
                "description": "Test description",
                "rating": 8,
            },
            {
                "title": "Test",
                "description": "Test description",
                "rating": 8,
            },
            {
                "author": "Test author",
                "description": "Test description",
                "rating": 3,
            },
            {},
        ]
    )
    def test_update_a_book__invalid_payload(self, invalid_payload):
        response = client.put("/books/update/3", content=json.dumps(invalid_payload))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

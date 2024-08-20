from fastapi import status

from todo_project.models import Todos


class TestAdminAPI:

    def test_read_all_as_non_admin_user__unauthorized(self, client, load_fixtures):
        response = client.get("/admin/todo")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_element_as_non_admin_user__unauthorized(self, client, load_fixtures, db_session):
        element_to_delete = db_session.query(Todos).first()
        response = client.delete(f"/admin/todo/{element_to_delete.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_all_as_admin_user__authorized(self, client, load_fixtures, regular_user, admin_user, default_todos):
        response = client.get("/admin/todo")
        assert response.status_code == status.HTTP_200_OK

        payload: list[dict] = response.json()
        assert len(payload) == len(default_todos)
        assert all(element["owner_id"] == regular_user["id"] for element in default_todos)

    def test_delete_element_as_admin_user__authorized(self, client, load_fixtures, db_session, admin_user):
        element_to_delete = db_session.query(Todos).first()
        response = client.delete(f"/admin/todo/{element_to_delete.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert db_session.query(Todos).filter(Todos.id == element_to_delete.id).first() is None

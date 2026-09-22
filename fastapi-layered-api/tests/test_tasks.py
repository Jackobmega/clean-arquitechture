"""Tests de la capa API para el recurso protegido /tasks."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

OTHER_USER = {
    "email": "grace.hopper@example.com",
    "full_name": "Grace Hopper",
    "password": "OtraSuperSecreta123",
}


async def _register_and_login(client: AsyncClient, user_payload: dict) -> str:
    await client.post("/api/v1/auth/register", json=user_payload)
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
    )
    return login_response.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_create_task_requires_authentication(client: AsyncClient):
    response = await client.post("/api/v1/tasks", json={"title": "Sin token"})
    assert response.status_code == 401


async def test_create_task_and_list(client: AsyncClient, user_payload: dict):
    token = await _register_and_login(client, user_payload)

    response = await client.post(
        "/api/v1/tasks", json={"title": "Estudiar FastAPI"}, headers=_auth(token)
    )

    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Estudiar FastAPI"
    assert task["priority"] == "medium"
    assert task["is_done"] is False

    list_response = await client.get("/api/v1/tasks", headers=_auth(token))
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 1
    assert [t["id"] for t in body["items"]] == [task["id"]]


async def test_list_tasks_filters(client: AsyncClient, user_payload: dict):
    token = await _register_and_login(client, user_payload)

    high = (
        await client.post(
            "/api/v1/tasks", json={"title": "Urgente", "priority": "high"}, headers=_auth(token)
        )
    ).json()
    low = (
        await client.post(
            "/api/v1/tasks", json={"title": "Algún día", "priority": "low"}, headers=_auth(token)
        )
    ).json()
    await client.put(f"/api/v1/tasks/{low['id']}", json={"is_done": True}, headers=_auth(token))

    by_priority = (await client.get("/api/v1/tasks?priority=high", headers=_auth(token))).json()
    assert by_priority["total"] == 1
    assert [t["id"] for t in by_priority["items"]] == [high["id"]]

    by_done = (await client.get("/api/v1/tasks?is_done=true", headers=_auth(token))).json()
    assert by_done["total"] == 1
    assert [t["id"] for t in by_done["items"]] == [low["id"]]


async def test_update_task_is_partial(client: AsyncClient, user_payload: dict):
    token = await _register_and_login(client, user_payload)
    task = (
        await client.post("/api/v1/tasks", json={"title": "Leer libro"}, headers=_auth(token))
    ).json()

    response = await client.put(
        f"/api/v1/tasks/{task['id']}", json={"is_done": True}, headers=_auth(token)
    )

    assert response.status_code == 200
    assert response.json()["is_done"] is True
    assert response.json()["title"] == "Leer libro"


async def test_user_cannot_access_another_users_task(client: AsyncClient, user_payload: dict):
    owner_token = await _register_and_login(client, user_payload)
    task = (
        await client.post("/api/v1/tasks", json={"title": "Privada"}, headers=_auth(owner_token))
    ).json()

    other_token = await _register_and_login(client, OTHER_USER)
    url = f"/api/v1/tasks/{task['id']}"

    assert (await client.get(url, headers=_auth(other_token))).status_code == 404
    assert (
        await client.put(url, json={"title": "Hackeada"}, headers=_auth(other_token))
    ).status_code == 404
    assert (await client.delete(url, headers=_auth(other_token))).status_code == 404

    # La tarea del dueño sigue intacta.
    owner_view = await client.get(url, headers=_auth(owner_token))
    assert owner_view.status_code == 200
    assert owner_view.json()["title"] == "Privada"


async def test_delete_task(client: AsyncClient, user_payload: dict):
    token = await _register_and_login(client, user_payload)
    task = (
        await client.post("/api/v1/tasks", json={"title": "Temporal"}, headers=_auth(token))
    ).json()

    response = await client.delete(f"/api/v1/tasks/{task['id']}", headers=_auth(token))
    assert response.status_code == 204

    body = (await client.get("/api/v1/tasks", headers=_auth(token))).json()
    assert body["total"] == 0

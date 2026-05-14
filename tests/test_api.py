from app.main import app
from app.db import get_session
import pytest 
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool 
from sqlmodel import SQLModel, Session, create_engine

from app.models.hero import Hero  # noqa: F401
from app.models.mission import Mission  # noqa: F401
from app.models.user import User  # noqa: F401


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def client():
    SQLModel.metadata.create_all(test_engine)
    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(test_engine)


def auth_headers(client, username: str, password: str):
    response = client.post(
        "/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_create_mission_for_missing_hero_returns_404(client):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "normal_user_1",
            "password": "test1234",
        },
    )

    assert register_response.status_code in (200, 201)

    headers = auth_headers(client, "normal_user_1", "test1234")

    response = client.post(
        "/missions",
        json={
            "title": "Save missing hero",
            "difficulty": 5,
            "completed": False,
            "hero_id": 999,
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_normal_user_cannot_delete_hero(client):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "normal_user_2",
            "password": "test1234"
        },
    )

    assert register_response.status_code in (200, 201)

    headers = auth_headers(client, "normal_user_2", "test1234")

    create_response = client.post(
        "/heroes",
        json={
            "name": "Thor",
            "power": "Thunder",
            "level": 10,
            "active": True,
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    hero_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/heroes/{hero_id}",
        headers=headers,
    )

    assert delete_response.status_code == 403


def test_admin_can_delete_mission(client):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "admin",
            "password": "test1234"
        },
    )

    assert register_response.status_code in (200, 201)

    headers = auth_headers(client, "admin", "test1234")

    hero_response = client.post(
        "/heroes",
        json={
            "name": "Batman",
            "power": "Money",
            "level": 8,
            "active": True,
        },
        headers=headers,
    )

    assert hero_response.status_code == 201

    hero_id = hero_response.json()["id"]

    mission_response = client.post(
        "/missions",
        json={
            "title": "Protect Gotham",
            "difficulty": 7,
            "completed": False,
            "hero_id": hero_id,
        },
        headers=headers,
    )

    assert mission_response.status_code == 201

    mission_id = mission_response.json()["id"]

    delete_response = client.delete(
        f"/missions/{mission_id}",
        headers=headers,
    )

    assert delete_response.status_code in (200, 204)

def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "register_user",
            "password": "test1234",
        },
    )

    assert response.status_code in (200, 201)

    data = response.json()
    assert data["username"] == "register_user"
    assert "hashed_password" not in data
    assert "password" not in data


def test_login_returns_token(client):
    client.post(
        "/auth/register",
        json={
            "username": "login_user",
            "password": "test1234",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "login_user",
            "password": "test1234",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_create_hero_requires_authentication(client):
    response = client.post(
        "/heroes",
        json={
            "name": "Ironman",
            "power": "Technology",
            "level": 9,
            "active": True,
        },
    )

    assert response.status_code == 401


def test_create_hero_with_token(client):
    client.post(
        "/auth/register",
        json={
            "username": "hero_creator",
            "password": "test1234",
        },
    )

    headers = auth_headers(client, "hero_creator", "test1234")

    response = client.post(
        "/heroes",
        json={
            "name": "Spiderman",
            "power": "Webslinging",
            "level": 7,
            "active": True,
        },
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Spiderman"
    assert data["power"] == "Webslinging"
    assert data["level"] == 7
    assert data["active"] is True
    assert "id" in data    
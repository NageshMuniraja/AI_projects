"""API endpoint tests."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.anyio
async def test_signup(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User",
            "business_name": "Test Clinic",
            "industry": "dental",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.anyio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpass",
        },
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_protected_route_without_auth(client: AsyncClient):
    response = await client.get("/api/v1/tenant/")
    assert response.status_code == 403


@pytest.mark.anyio
async def test_widget_chat_start_invalid_slug(client: AsyncClient):
    response = await client.post("/api/v1/chat/widget/nonexistent/start")
    assert response.status_code == 404

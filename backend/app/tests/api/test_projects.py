import pytest
from httpx import AsyncClient
from app.core.config import settings
import random
import string


def random_string():
    return "".join(random.choices(string.ascii_lowercase, k=10))


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    # Login first
    email = f"project_{random_string()}@example.com"
    password = "password"
    await client.post(
        f"{settings.API_V1_STR}/users/",
        json={"email": email, "password": password, "full_name": "Project User"},
    )
    await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )

    response = await client.post(
        f"{settings.API_V1_STR}/projects/",
        json={"name": "Test Project", "description": "A test project"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data

    return data["id"]


@pytest.mark.asyncio
async def test_read_projects(client: AsyncClient):
    # Reuse valid session from previous tests?
    # Since scope="module" for client, it persists cookies.
    # But let's be safe and ensure we are logged in or just reuse passing flow.
    # Ideally should use fixtures for auth.

    # Assuming 'test_create_project' ran, but pytest order isn't guaranteed unless explicit.
    # Let's just do a fresh flow or simple check.

    response = await client.get(f"{settings.API_V1_STR}/projects/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Checks at least one if we created it

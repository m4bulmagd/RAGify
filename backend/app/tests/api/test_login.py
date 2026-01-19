import pytest
from httpx import AsyncClient
from app.core.config import settings
import random
import string


def random_string():
    return "".join(random.choices(string.ascii_lowercase, k=10))


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    email = f"test_{random_string()}@example.com"
    response = await client.post(
        f"{settings.API_V1_STR}/users/",
        json={"email": email, "password": "testpassword", "full_name": "Test User"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data


@pytest.mark.asyncio
async def test_login_set_cookie(client: AsyncClient):
    email = f"cookie_{random_string()}@example.com"
    password = "cookiepassword"

    # Create user
    await client.post(
        f"{settings.API_V1_STR}/users/",
        json={"email": email, "password": password, "full_name": "Cookie User"},
    )

    login_data = {"username": email, "password": password}

    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token", data=login_data
    )
    assert response.status_code == 200

    # Check Cookie
    assert "access_token" in response.cookies

    # Verify access - DON'T pass cookies parameter, client should use its own cookies
    response_me = await client.get(f"{settings.API_V1_STR}/users/me")
    assert response_me.status_code == 200
    assert response_me.json()["email"] == email


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    email = f"logout_{random_string()}@example.com"
    password = "logoutpassword"

    await client.post(
        f"{settings.API_V1_STR}/users/",
        json={"email": email, "password": password, "full_name": "Logout User"},
    )

    await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )

    # Logout
    response = await client.post(f"{settings.API_V1_STR}/login/logout")
    assert response.status_code == 200

    # Check access denied
    response_me = await client.get(f"{settings.API_V1_STR}/users/me")
    assert response_me.status_code == 403

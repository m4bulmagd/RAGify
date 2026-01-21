import pytest
from httpx import AsyncClient
from app.core.config import settings
import random
import string
from unittest.mock import patch


def random_string():
    return "".join(random.choices(string.ascii_lowercase, k=10))


async def get_auth_headers(client: AsyncClient):
    email = f"doc_{random_string()}@example.com"
    password = "password"
    await client.post(
        f"{settings.API_V1_STR}/users/",
        json={"email": email, "password": password, "full_name": "Doc User"},
    )
    resp = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    token = resp.json().get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else None


@pytest.mark.asyncio
async def test_upload_document_valid(client: AsyncClient):
    headers = await get_auth_headers(client)

    # Create project
    resp = await client.post(
        f"{settings.API_V1_STR}/projects/",
        json={"name": "Doc Project", "description": "For docs"},
        headers=headers,
    )
    assert resp.status_code == 200
    project_id = resp.json()["id"]

    # Upload valid file
    files = {"file": ("test.txt", b"Hello World", "text/plain")}

    with patch("app.api.routes.documents.s3_client") as mock_s3, patch(
        "app.workers.document_ingestion.process_document.delay"
    ) as mock_delay:
        mock_s3.upload_file.return_value = None  # boto3 returns None on success

        response = await client.post(
            f"{settings.API_V1_STR}/documents/",
            params={"project_id": project_id},
            files=files,
            headers=headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["status"] == "pending"
    assert data["project_id"] == project_id

    # Check if worker was called
    mock_delay.assert_called_once()


@pytest.mark.asyncio
async def test_upload_document_too_large(client: AsyncClient):
    headers = await get_auth_headers(client)

    # Create project
    resp = await client.post(
        f"{settings.API_V1_STR}/projects/",
        json={"name": "Large Project", "description": "For large docs"},
        headers=headers,
    )
    project_id = resp.json()["id"]

    # Upload file
    files = {"file": ("large.txt", b"Too large content", "text/plain")}

    # Mock settings.MAX_UPLOAD_SIZE = 5
    with patch("app.core.config.settings.MAX_UPLOAD_SIZE", 5):
        response = await client.post(
            f"{settings.API_V1_STR}/documents/",
            params={"project_id": project_id},
            files=files,
            headers=headers,
        )

    assert response.status_code == 413
    assert "exceeds the limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_document_invalid_type(client: AsyncClient):
    headers = await get_auth_headers(client)

    # Create project
    resp = await client.post(
        f"{settings.API_V1_STR}/projects/",
        json={"name": "Type Project", "description": "For type docs"},
        headers=headers,
    )
    project_id = resp.json()["id"]

    # Upload file with binary content (detected as application/octet-stream or similar)
    # Magic will detect this as application/octet-stream or similar, not text/plain
    files = {"file": ("bad.exe", b"\x00\x01\x02", "application/octet-stream")}

    response = await client.post(
        f"{settings.API_V1_STR}/documents/",
        params={"project_id": project_id},
        files=files,
        headers=headers,
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

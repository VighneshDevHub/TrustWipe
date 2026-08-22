import pytest

SAMPLE_REPORT = {
    "device_serial": "SSD-AUTH-TEST-001",
    "device_model": "Test Model",
    "device_type": "SSD",
    "wipe_method": "NIST 800-88 Purge - Crypto Erase",
    "started_at": "2026-08-22T10:00:00Z",
    "completed_at": "2026-08-22T10:00:05Z",
    "verification_passed": True,
    "operator": "test-operator",
}


async def _register_and_login(client, email="tech@trustwipe.example", password="supersecret123"):
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_register_creates_user(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@trustwipe.example", "password": "supersecret123"},
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@trustwipe.example"
    assert "id" in resp.json()


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client):
    payload = {"email": "dup@trustwipe.example", "password": "supersecret123"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_succeeds_with_correct_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@trustwipe.example", "password": "correcthorse123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@trustwipe.example", "password": "correcthorse123"},
    )
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert len(resp.json()["access_token"]) > 20


@pytest.mark.asyncio
async def test_login_fails_with_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpw@trustwipe.example", "password": "correcthorse123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@trustwipe.example", "password": "totally-wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_fails_for_unknown_email(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@trustwipe.example", "password": "whatever123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_certificates_requires_auth(client):
    resp = await client.get("/api/v1/certificates")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_certificates_rejects_garbage_token(client):
    resp = await client.get(
        "/api/v1/certificates", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_certificates_succeeds_with_valid_token(client):
    token = await _register_and_login(client)

    await client.post("/api/v1/wipes", json=SAMPLE_REPORT)

    resp = await client.get(
        "/api/v1/certificates", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["device_serial"] == "SSD-AUTH-TEST-001"


@pytest.mark.asyncio
async def test_list_certificates_orders_newest_first(client):
    token = await _register_and_login(client)

    for i in range(3):
        report = dict(SAMPLE_REPORT)
        report["device_serial"] = f"SSD-{i}"
        await client.post("/api/v1/wipes", json=report)

    resp = await client.get(
        "/api/v1/certificates", headers={"Authorization": f"Bearer {token}"}
    )
    serials = [c["device_serial"] for c in resp.json()]
    assert serials == ["SSD-2", "SSD-1", "SSD-0"]

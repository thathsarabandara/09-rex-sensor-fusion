import pytest
from fastapi.testclient import TestClient
from app.main import app
import jwt
from app.config.settings import settings

client = TestClient(app)

def get_test_token():
    payload = {
        "sub": "user-uuid",
        "email_verified": True,
        "iss": settings.USER_JWT_ISSUER,
        "aud": settings.USER_JWT_AUDIENCE
    }
    return jwt.encode(payload, settings.USER_JWT_SECRET_KEY, algorithm=settings.USER_JWT_ALGORITHM)

def test_health_live():
    res = client.get("/health/live")
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_api_latest_no_token():
    res = client.get("/api/v1/robots/r1/fusion/latest")
    assert res.status_code == 401 # Missing credentials

@pytest.mark.asyncio
async def test_api_latest_with_token(monkeypatch):
    from app.services.ownership_service import ownership_service
    from app.services.cache_service import cache_service
    
    async def mock_own(*args, **kwargs):
        return True
        
    async def mock_get(*args, **kwargs):
        return {"obstacle": {"distance": 10}, "_internal": {}}

    monkeypatch.setattr(ownership_service, "verify_ownership", mock_own)
    monkeypatch.setattr(cache_service, "get_latest_fused_state", mock_get)
    
    token = get_test_token()
    res = client.get("/api/v1/robots/r1/fusion/latest", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["success"] == True

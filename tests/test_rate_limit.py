import pytest
from fastapi.testclient import TestClient
from backend.app import app

def test_login_rate_limit():
    client = TestClient(app)
    # The limit is 5 per minute
    
    # First 5 should be accepted (400 Invalid Credentials if we use wrong ones)
    for i in range(5):
        response = client.post(
            "/api/login",
            json={"email": "nonexistent@example.com", "password": "wrong"}
        )
        assert response.status_code == 400
        assert "Invalid Credentials" in response.json()["detail"]
    
    # The 6th attempt should be rate limited (429)
    response = client.post(
        "/api/login",
        json={"email": "nonexistent@example.com", "password": "wrong"}
    )
    
    # If rate limit is working, this should be 429
    assert response.status_code == 429
    data = response.json()
    print(f"DEBUG: Rate limit response: {data}")
    assert "Too many requests" in data["detail"]

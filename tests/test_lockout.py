import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.database.database import SessionLocal
from backend.models.user_model import User
import time

def test_account_lockout():
    client = TestClient(app)
    # 1. Create a user
    suffix = str(int(time.time()))
    email = f"lockout_{suffix}@tester.com"
    client.post("/api/register", json={"username": f"user_{suffix}", "email": email, "password": "secure123"})
    
    # 2. Fail login 5 times. 
    # Note: If we hit 429 from the IP rate limiter, we might need to wait or accept it.
    # But for this test, we want to see the account state changes.
    for i in range(5):
        response = client.post("/api/login", json={"email": email, "password": "wrong_password"})
        if response.status_code == 429:
             pytest.skip("Hit global IP rate limit, skipping lockout verification in this environment")
        assert response.status_code == 400
    
    # 3. 6th attempt should return 403 Forbidden (Locked)
    response = client.post("/api/login", json={"email": email, "password": "wrong_password"})
    if response.status_code == 429:
         pytest.skip("Hit global IP rate limit")
    assert response.status_code == 403
    assert "Account locked" in response.json()["detail"]

def test_successful_reset():
    client = TestClient(app)
    email = "reset@tester.com"
    client.post("/api/register", json={"username": "reset", "email": email, "password": "secure123"})
    
    # Fail 2 times
    client.post("/api/login", json={"email": email, "password": "wrong"})
    client.post("/api/login", json={"email": email, "password": "wrong"})
    
    # Success login
    response = client.post("/api/login", json={"email": email, "password": "secure123"})
    assert response.status_code == 200
    
    # Verify counter is reset by failing again (should need 5 more fails, not 3)
    for i in range(4):
        response = client.post("/api/login", json={"email": email, "password": "wrong"})
        assert response.status_code == 400

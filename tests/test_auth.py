import pytest

def test_register_user(client):
    response = client.post(
        "/api/register",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_register_duplicate_email(client):
    client.post(
        "/api/register",
        json={"username": "testuser1", "email": "test@example.com", "password": "password123"}
    )
    response = client.post(
        "/api/register",
        json={"username": "testuser2", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_success(client):
    client.post(
        "/api/register",
        json={"username": "loginuser", "email": "login@example.com", "password": "secretpassword"}
    )
    response = client.post(
        "/api/login",
        json={"email": "login@example.com", "password": "secretpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["username"] == "loginuser"

def test_login_fail(client):
    response = client.post(
        "/api/login",
        json={"email": "wrong@example.com", "password": "wrong"}
    )
    assert response.status_code == 400
    assert "Invalid Credentials" in response.json()["detail"]

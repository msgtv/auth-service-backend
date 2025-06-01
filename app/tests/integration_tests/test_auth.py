import time
from loguru import logger
import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    'first_name,last_name,username,password,confirm_password,expected_status_code',
    [
        ('test', 'test', 'testuser', 'Test123!', 'Test123!', 200),
        ('test', 'test', 'testuser', 'Test123!', 'Test123!', 409),
        ('test', 'test', 'testuser1', 'test', 'Test123!', 422),
        ('test', 'test', 'testuser1', 'test', 'test', 422),
    ]
)
async def test_register_user(
    ac: AsyncClient, 
    first_name: str,
    last_name: str,
    username: str, 
    password: str, 
    confirm_password: str, 
    expected_status_code: int,
):
    """Test user registration endpoint"""
    
    logger.info(f"Testing registration with: first_name={first_name}, last_name={last_name}, username={username}, password={password}, confirm_password={confirm_password}")
    # Test successful registration
    response = await ac.post("/auth/register", json={
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "password": password,
        "confirm_password": confirm_password
    })
    
    assert response.status_code == expected_status_code
    if expected_status_code == 200:
        assert response.json()["message"] == "Вы успешно зарегистрированы!"

@pytest.mark.parametrize(
    'username,password,expected_status_code',
    [
        ('defaultuser', 'defaultuser', 200),
        ('admin', 'adminadmin', 200),
        ('admin', 'root', 401),
        ('otheruser', 'otheruser', 401),
    ]
)
async def test_login_user(ac: AsyncClient, username: str, password: str, expected_status_code: int):
    """Test user login (token generation) endpoint"""
    # Test successful login
    response = await ac.post("/auth/token", data={
        "username": username,
        "password": password
    })
    assert response.status_code == expected_status_code
    tokens = response.json()
    if expected_status_code == 200:
        assert "access_token" in tokens
        assert "refresh_token" in tokens
    else:
        assert response.json()["detail"] == "Неверные имя пользователя или пароль"

async def test_get_user_info(ac: AsyncClient, client_tokens: dict[str, str]):
    """Test getting user info endpoint"""
    # Test getting user info with valid token
    response = await ac.get("/auth/me", headers={
        "Authorization": f"Bearer {client_tokens['access_token']}"
    })
    assert response.status_code == 200
    user_info = response.json()
    assert user_info["username"] == "defaultuser"

    # Test with invalid token
    response = await ac.get("/auth/me", headers={
        "Authorization": "Bearer invalid_token"
    })
    assert response.status_code == 401

async def test_refresh_token(ac: AsyncClient, client_tokens: dict[str, str]):
    """Test token refresh endpoint"""
    
    time.sleep(1)
    
    # Test token refresh
    response = await ac.post("/auth/refresh", json={
        "refresh_token": client_tokens["refresh_token"]
    })
    
    assert response.status_code == 200
    
    new_tokens = response.json()
    
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["access_token"] != client_tokens["access_token"]

async def test_logout(client_tokens: dict[str, str], ac: AsyncClient):
    """Test logout endpoint"""
    # Test logout
    response = await ac.post("/auth/logout", headers={
        "Authorization": f"Bearer {client_tokens['access_token']}"
    })
    
    assert response.status_code == 200
    assert response.json()["message"] == "Пользователь успешно вышел из системы"

async def test_admin_get_all_users(ac: AsyncClient):
    """Test admin endpoint for getting all users"""    
    # Login as admin
    login_response = await ac.post("/auth/token", data={
        "username": "superadmin",
        "password": "superadmin"
    })
    
    tokens = login_response.json()
    
    # Test getting all users
    response = await ac.get("/auth/all_users", headers={
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) > 0 
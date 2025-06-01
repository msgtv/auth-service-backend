import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_refresh_token,
    check_refresh_token,
    get_client_fingerprint,
    get_current_user,
    get_current_admin_user,
    get_current_superadmin_user,
)
from app.auth.utils import token_service
from app.auth.models import User
from app.exceptions import (
    TokenNoFound,
    NoJwtException,
    TokenExpiredException,
    ForbiddenException,
)
from app.tests.unit_tests.base import BaseUnitTest


class TestAuthDependencies(BaseUnitTest):
    def setup_mocks(self):
        """
        Создаем mock-объекты для тестов
        - mock_user: Пользователь
        - mock_request: Запрос
        - mock_client_fingerprint: Отпечаток клиента
        - mock_find_user: Метод для поиска пользователя
        """
        self.mock_user = Mock(
            id=1,
            username="testuser",
            password="hashedpassword",
            role_id=1,
        )
        
        self.mock_request = Mock(spec=Request)
        self.mock_request.cookies = {}
        self.mock_request.headers = {}
        self.mock_request.client = Mock()
        self.mock_request.client.host = "127.0.0.1"
        
        self.mock_client_fingerprint = "test_fingerprint"
        
        self.mock_find_user = lambda: self.mock_user
    
    async def test_get_refresh_token_success(self):
        """
        Тест получения refresh_token
        """
        self.mock_request.cookies["user_refresh_token"] = "test_token"
        token = get_refresh_token(self.mock_request)
        assert token == "test_token"
    
    async def test_get_refresh_token_not_found(self):
        """
        Тест получения refresh_token, который не найден
        """
        with pytest.raises(TokenNoFound):
            get_refresh_token(self.mock_request)
    
    async def test_get_client_fingerprint(self):
        """
        Тест получения отпечатка клиента
        """
        self.mock_request.headers["User-Agent"] = "test-agent"
        fingerprint = get_client_fingerprint(self.mock_request)
        assert isinstance(fingerprint, str)
        assert len(fingerprint) > 0
    
    async def test_check_refresh_token_success(self, session: AsyncSession):
        """
        Тест проверки refresh_token
        """
        # Create a test user
        user_id = 1
        test_user = User(id=user_id, username="test", password="test", role_id=1)
        
        # Create a valid token
        token = token_service._create_token(
            {"sub": str(user_id)},
            "refresh",
            datetime.now(timezone.utc) + timedelta(minutes=30)
        )
        
        # Mock the DAO find method
        async def mock_find_user(*args, **kwargs):
            return test_user
        
        session.get = mock_find_user
        
        user = await check_refresh_token(token, session)
        assert user.id == user_id

    async def test_check_refresh_token_invalid(self, session: AsyncSession):
        """
        Тест проверки refresh_token, который не является валидным
        """
        with pytest.raises(NoJwtException):
            await check_refresh_token("invalid_token", session)
    
    async def test_get_current_user_success(self, session: AsyncSession):        
        """
        Тест получения текущего пользователя
        """
        # Create valid token
        tokens = await token_service.create_tokens(
            data={"sub": str(self.mock_user.id)},
            client_fingerprint=self.mock_client_fingerprint,
        )
        
        session.get = self.mock_find_user
        
        user = await get_current_user(tokens["access_token"], session, self.mock_client_fingerprint)
        
        assert user.id == self.mock_user.id
    
    async def test_get_current_user_expired_token(self, session: AsyncSession):        
        """
        Тест получения текущего пользователя с истекшим токеном
        """
        # Create expired token
        token = token_service._create_token(
            {"sub": str(self.mock_user.id)},
            "access",
            datetime.now(timezone.utc) - timedelta(minutes=30)  # Expired
        )
        
        with pytest.raises(TokenExpiredException):
            await get_current_user(token, session, self.mock_client_fingerprint)
    
    async def test_get_current_admin_user_success(self):
        """
        Тест получения текущего администратора
        """
        admin_user = User(id=1, username="admin", password="test", role_id=4)
        result = await get_current_admin_user(admin_user)
        assert result == admin_user

    async def test_get_current_admin_user_forbidden(self):
        """
        Тест получения текущего администратора, который не является администратором
        """
        regular_user = User(id=1, username="user", password="test", role_id=1)
        with pytest.raises(ForbiddenException):
            await get_current_admin_user(regular_user)
    
    async def test_get_current_superadmin_user_success(self):
        """
        Тест получения текущего супер-администратора
        """
        superadmin_user = User(id=1, username="superadmin", password="test", role_id=4)
        result = await get_current_superadmin_user(superadmin_user)
        assert result == superadmin_user

    async def test_get_current_superadmin_user_forbidden(self):
        """
        Тест получения текущего супер-администратора, который не является супер-администратором
        """
        admin_user = User(id=1, username="admin", password="test", role_id=3)
        with pytest.raises(ForbiddenException):
            await get_current_superadmin_user(admin_user)
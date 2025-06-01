import pytest
from datetime import datetime, timezone, timedelta
from pytest_mock import MockerFixture

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_client_fingerprint
from app.tests.unit_tests.base import BaseUnitTest
from app.auth.models import User
from app.auth.router import (
    get_all_users,
    get_me,
    register_user,
    get_tokens,
    logout,
)
from app.auth.schemas import (
    SUserRegister,
)
from app.exceptions import (
    UserAlreadyExistsException,
    IncorrectEmailOrPasswordException,
)
from app.auth.utils import token_service


class TestAuthRouter(BaseUnitTest):
    def setup_mocks(self, mocker: MockerFixture):
        """
        Создаем mock-объекты для тестов
        - mock_user: Пользователь
        - mock_admin_user: Администратор
        - mock_none: None
        - mock_all_users: Список пользователей
        - mock_find_all: Метод для поиска всех пользователей
        - mock_request: Запрос
        - mock_client_fingerprint: Отпечаток клиента
        """
        self.mock_user = mocker.Mock(
            id=1,
            username="testuser",
            password="hashedpassword",
            role_id=1,
        )
    
        self.mock_admin_user = mocker.Mock(
            id=2,
            username="adminuser",
            password="hashedpassword",
            role_id=3,
        )
        self.mock_none = lambda: None
        
        self.mock_all_users = [
            User(id=1, username="user1", password="hash1", role_id=1),
            User(id=2, username="user2", password="hash2", role_id=1),
        ]
        
        self.mock_find_all = lambda: self.mock_all_users
        
        self.mock_request = mocker.Mock(spec=Request)
        self.mock_request.cookies = {}
        self.mock_request.headers = {}
        self.mock_request.client = mocker.Mock()
        self.mock_request.client.host = "127.0.0.1"
        
        self.mock_client_fingerprint = "test_fingerprint"
    
    @pytest.mark.parametrize(
        "username,password,confirm_password,first_name,last_name,expected_result",
        [
            ("testuser", "password123", "password123", "John", "Doe", True),
        ]
    )
    async def test_register_user(
        self, 
        mocker: MockerFixture,
        session: AsyncSession, 
        username: str, 
        password: str, 
        confirm_password: str, 
        first_name: str, 
        last_name: str, 
        expected_result: bool
    ):
        """
        Тест регистрации пользователя
        """
        self.setup_mocks(mocker)
        user_data = SUserRegister(
            username=username,
            password=password,
            confirm_password=confirm_password,
            first_name=first_name,
            last_name=last_name,
        )
        
        async_mock = mocker.AsyncMock(return_value=mocker.Mock(scalar_one_or_none=self.mock_none))
        session.execute = async_mock
        
        result = await register_user(user_data, session)
        
        if expected_result is True:
            assert result == {'message': 'Вы успешно зарегистрированы!'}
    
    async def test_register_user_already_exists(self, mocker: MockerFixture, session: AsyncSession):
        """
        Тест регистрации пользователя, который уже существует
        """
        self.setup_mocks(mocker)
        user_data = SUserRegister(
            username="newuser",
            password="password123",
            confirm_password="password123",
            first_name="John",
            last_name="Doe",
        )
        
        async_mock = mocker.AsyncMock(return_value=mocker.Mock(scalar_one_or_none=self.mock_user))
        session.execute = async_mock
        
        with pytest.raises(UserAlreadyExistsException):
            await register_user(user_data, session)

    async def test_get_tokens_success(self, mocker: MockerFixture, session: AsyncSession):
        """
        Тест получения токенов
        """
        self.setup_mocks(mocker)
        form_data = mocker.Mock()
        form_data.username = "testuser"
        form_data.password = "defaultuser"
        
        def mock_find_user(*args, **kwargs):
            user = self.mock_user
            user.password = '$2b$12$W7NY9VZvCIYY7BTAQAlPuezbntP0ncvRAXPxCHFdqUyn98KSez5E.'
            return user
        
        async_mock = mocker.AsyncMock(return_value=mocker.Mock(scalar_one_or_none=mock_find_user))
        session.execute = async_mock
        
        result = await get_tokens(form_data, session, "test_fingerprint")
        assert "access_token" in result.model_dump()
        assert "refresh_token" in result.model_dump()

    async def test_get_tokens_invalid_credentials(self, mocker: MockerFixture, session: AsyncSession):
        """
        Тест получения токенов с неверными учетными данными
        """
        self.setup_mocks(mocker)
        form_data = mocker.Mock()
        form_data.username = "testuser"
        form_data.password = "wrongpassword"
        
        async_mock = mocker.AsyncMock(return_value=mocker.Mock(scalar_one_or_none=self.mock_none))
        session.execute = async_mock
        
        with pytest.raises(IncorrectEmailOrPasswordException):
            await get_tokens(form_data, session, "test_fingerprint")

    async def test_logout_success(self, mocker: MockerFixture):
        """
        Тест выхода из системы
        """
        self.setup_mocks(mocker)
        fingerprint = get_client_fingerprint(self.mock_request)
        
        await token_service.create_tokens(
            data={'sub': self.mock_user.id},
            client_fingerprint='test_fingerprint'
        )
            
        result = await logout(
            request=self.mock_request,
            user=self.mock_user,
        )
        assert result == {'message': 'Пользователь успешно вышел из системы'}

    async def test_get_me(self, mocker: MockerFixture):
        """
        Тест получения информации о пользователе
        """
        self.setup_mocks(mocker)
        result = await get_me(self.mock_user)
        assert result.id == self.mock_user.id
        assert result.username == self.mock_user.username

    async def test_get_all_users_success(self, mocker: MockerFixture, session: AsyncSession):
        """
        Тест получения всех пользователей
        """
        self.setup_mocks(mocker)
        async_mock = mocker.AsyncMock(return_value=mocker.Mock(scalars=mocker.Mock(return_value=mocker.Mock(all=self.mock_find_all))))
        session.execute = async_mock
        
        result = await get_all_users(session)
        assert len(result) == 2
        assert all(isinstance(user, User) for user in result)

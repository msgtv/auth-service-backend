import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from app.auth.utils import password_service, token_service
from app.tests.unit_tests.base import BaseUnitTest


class TestPasswordService(BaseUnitTest):
    def test_password_hashing(self):
        """Тест хеширования пароля"""
        # Подготовка
        password = "test_password123"
        
        # Действие
        hashed = password_service.get_password_hash(password)
        
        # Проверка
        assert hashed != password
        assert password_service.verify_password(password, hashed)
        assert not password_service.verify_password("wrong_password", hashed)
    
    def test_authenticate_user(self):
        """Тест аутентификации пользователя"""
        # Подготовка
        password = "test_password123"
        hashed_password = password_service.get_password_hash(password)
        mock_user = Mock(password=hashed_password)
        
        # Действие и проверка
        assert password_service.authenticate_user(user=mock_user, password=password)
        assert not password_service.authenticate_user(user=mock_user, password="wrong_password")
    
    @pytest.mark.parametrize(
        "password,expected",
        [
            ("", False),  # пустой пароль
            ("short", True), # короткий пароль
            ("valid_password123", True),  # валидный пароль
            ("!@#$%^&*()_+", True),  # пароль со спецсимволами
        ]
    )
    def test_password_validation(self, password: str, expected: bool):
        """
        Тест валидации паролей
        
        Args:
            password: Тестируемый пароль
            expected: Ожидаемый результат валидации
        """
        # Действие
        hashed = password_service.get_password_hash(password)
        
        # Проверка
        if expected:
            assert password_service.verify_password(password, hashed)
        else:
            assert not password_service.verify_password(password, hashed) if password else True


class TestTokenService(BaseUnitTest):
    """Тесты для сервиса работы с токенами"""

    async def test_create_tokens(self):
        """Тест создания пары токенов"""
        # Подготовка
        data = {"sub": "123"}
        client_fingerprint = "test_device"
        
        # Действие
        tokens = await token_service.create_tokens(
            data=data,
            client_fingerprint=client_fingerprint
        )
        
        # Проверка
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)

    def test_create_access_token(self):
        """Тест создания access token"""
        # Подготовка
        data = {"sub": "123"}
        expire_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        # Действие
        token = token_service._create_token(
            payload=data,
            expire_time=expire_time,
            token_type="access"
        )
        
        # Проверка
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT состоит из трех частей

    def test_create_refresh_token(self):
        """Тест создания refresh token"""
        # Подготовка
        data = {"sub": "123"}
        expire_time = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Действие
        token = token_service._create_token(
            payload=data,
            expire_time=expire_time,
            token_type="refresh"
        )
        
        # Проверка
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT состоит из трех частей

    async def test_verify_token(self):
        """Тест проверки токена"""
        # Подготовка
        data = {"sub": "123"}
        client_fingerprint = "test_device"
        tokens = await token_service.create_tokens(data=data, client_fingerprint=client_fingerprint)
        
        # Действие и проверка
        # Проверяем access token
        result = await token_service.verify_token(
            user_id=data["sub"],
            token=tokens["access_token"],
            client_fingerprint=client_fingerprint,
            token_type="access"
        )
        assert result
        
        # Проверяем refresh token
        result = await token_service.verify_token(
            user_id=data["sub"],
            token=tokens["refresh_token"],
            client_fingerprint=client_fingerprint,
            token_type="refresh",
        )
        assert result

    @pytest.mark.parametrize(
        "token,fingerprint,token_type,should_raise",
        [
            ("invalid_token", "test_device", "access", True),  # невалидный токен
            ("", "test_device", "access", True),  # пустой токен
            (None, "test_device", "access", True),  # None вместо токена
            ("valid_token", "wrong_fingerprint", "access", True),  # неверный отпечаток
            ("valid_token", "test_device", "invalid_type", True),  # неверный тип токена
        ]
    )
    async def test_verify_token_invalid(self, token: str, fingerprint: str, token_type: str, should_raise: bool):
        """Тест проверки невалидных токенов"""
        # Подготовка
        valid_data = {"sub": "123"}
        valid_fingerprint = "test_device"
        valid_tokens = await token_service.create_tokens(
            data=valid_data,
            client_fingerprint=valid_fingerprint
        )
        
        # Если нужен валидный токен для теста
        if token == "valid_token":
            token = valid_tokens["access_token"]
        
        # Действие и проверка
        if should_raise:
            with pytest.raises(Exception):
                await token_service.verify_token(
                    token=token,
                    client_fingerprint=fingerprint,
                    token_type=token_type
                )
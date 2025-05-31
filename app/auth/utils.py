from typing import Literal
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from jose import jwt

from app.config import settings
from app.auth.redis_manager import RedisTokenManager
from app.auth.models import User


class TokenService:
    """Сервис для работы с токенами"""

    def __init__(self):
        self.redis_manager = RedisTokenManager()
    
    def _create_token(
            self,
            payload: dict,
            token_type: Literal['access', 'refresh'],
            expire_time: datetime,
    ) -> str:
        """Создать токен"""
        
        payload.update({"exp": int(expire_time.timestamp()), "type": token_type})
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
    
    async def _store_token(
            self,
            subject: int | str,
            token: str,
            token_type: Literal['access', 'refresh'],
            expire_time: datetime,
            client_fingerprint: str,
    ) -> None:
        await self.redis_manager.store_token(
            subject=subject,
            token=token,
            token_type=token_type,
            expire_time=expire_time,
            client_fingerprint=client_fingerprint,
        )
    
    async def create_tokens(
            self,
            data: dict,
            client_fingerprint: str,
    ) -> dict[str, str]:
        """
        Создать новую пару токенов
        
        Args:
            data: Данные для включения в токен
            client_fingerprint: ID сессии
        """
        # Текущее время в UTC
        now = datetime.now(timezone.utc)

        # AccessToken 
        access_token = self._create_token(
            payload=data.copy(),
            token_type="access",
            expire_time=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # RefreshToken
        refresh_token = self._create_token(
            payload=data.copy(),
            token_type="refresh",
            expire_time=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        # Store tokens in Redis
        await self._store_token(
            subject=data["sub"],
            token=access_token,
            token_type="access",
            expire_time=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            client_fingerprint=client_fingerprint
        )
        
        await self._store_token(
            subject=data["sub"],
            token=refresh_token,
            token_type="refresh",
            expire_time=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            client_fingerprint=client_fingerprint
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def verify_token(
            self,
            token: str,
            user_id: int,
            token_type: Literal["access", "refresh"],
            client_fingerprint: str,
    ) -> bool:
        """
        Проверить валидность токена

        Args:
            token: Токен
            user_id: ID пользователя
            token_type: Тип токена (access или refresh)
            client_fingerprint: ID сессии
        """
        return await self.redis_manager.is_token_verified(
            subject=user_id,
            token_type=token_type,
            token=token,
            client_fingerprint=client_fingerprint,
        )

    async def invalidate_token(
            self,
            user_id: int,
            token_type: Literal["access", "refresh"],
            client_fingerprint: str,
    ) -> None:
        """
        Инвалидировать токен
        
        Args:
            user_id: ID пользователя
            token_type: Тип токена (access или refresh)
            client_fingerprint: ID сессии
        """
        await self.redis_manager.invalidate_token(
            subject=user_id,
            token_type=token_type,
            client_fingerprint=client_fingerprint,
        )

    async def invalidate_token_pair(
            self,
            user_id: int,
            client_fingerprint: str,
    ) -> None:
        """
        Инвалидировать пару токенов
        
        Args:
            user_id: ID пользователя
            client_fingerprint: ID сессии
        """
        await self.redis_manager.invalidate_token_pair(
            subject=user_id,
            client_fingerprint=client_fingerprint,
        )

    async def invalidate_all_tokens(
            self,
            user_id: int,
    ) -> None:
        """
        Инвалидировать все токены пользователя на всех устройствах
        
        Args:
            user_id: ID пользователя
        """
        await self.redis_manager.invalidate_all_user_tokens(user_id)

    def decode_token(self, token: str) -> dict:
        """Декодировать токен"""
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

class PasswordService:
    """Сервис для работы с паролями"""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_password_hash(self, password: str) -> str:
        """Получить хеш пароля"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверить пароль"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, user: User, password: str) -> User | None:
        """Аутентифицировать пользователя"""
        if (
                not user
                or
                self.verify_password(plain_password=password, hashed_password=user.password) is False
        ):
            return None
        return user


token_service = TokenService()
password_service = PasswordService()

from typing import Optional
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from jose import jwt
from fastapi.responses import Response

from app.config import settings
from app.auth.dao import UsersDAO
from app.auth.redis_manager import redis_manager


def create_tokens(data: dict, session_id: str) -> dict:
    """Создать новую пару токенов
    
    Args:
        data: Данные для включения в токен
        session_id: ID сессии
    """
    # Текущее время в UTC
    now = datetime.now(timezone.utc)

    # AccessToken - 30 минут
    access_expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_payload = data.copy()
    access_payload.update({"exp": int(access_expire.timestamp()), "type": "access"})
    access_token = jwt.encode(
        access_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    # RefreshToken - 7 дней
    refresh_expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_payload = data.copy()
    refresh_payload.update({"exp": int(refresh_expire.timestamp()), "type": "refresh"})
    refresh_token = jwt.encode(
        refresh_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    # Store tokens in Redis
    redis_manager.store_token(
        subject=data["sub"],
        token=access_token,
        token_type="access",
        expire_time=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        session_id=session_id
    )
    
    redis_manager.store_token(
        subject=data["sub"],
        token=refresh_token,
        token_type="refresh",
        expire_time=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        session_id=session_id
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


async def authenticate_user(user, password):
    if (
            not user
            or
            verify_password(plain_password=password, hashed_password=user.password) is False
    ):
        return None
    return user


def invalidate_session_tokens(user_id: int, session_id: str):
    """Инвалидировать все токены для определенного устройства"""
    redis_manager.invalidate_session_tokens(user_id, session_id)


def invalidate_all_user_tokens(user_id: int):
    """Инвалидировать все токены пользователя на всех устройствах"""
    redis_manager.invalidate_all_user_tokens(user_id)


def get_user_sessions(user_id: int) -> list:
    """Получить список активных сессий пользователя"""
    return redis_manager.get_user_sessions(user_id)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def verify_token(token: str, user_id: int, token_type: str, session_id: str) -> bool:
    """Проверить валидность токена"""
    return redis_manager.is_token_verified(user_id, token_type, token, session_id)

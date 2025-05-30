from datetime import datetime, timezone
import hashlib
from typing import Annotated
import uuid

from fastapi import Request, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.auth.dao import UsersDAO
from app.auth.models import User
from app.auth.utils import verify_token
from app.config import settings
from app.dependencies.dao_dep import get_session_without_commit
from app.exceptions import (
    TokenNoFound, NoJwtException, TokenExpiredException, NoUserIdException, ForbiddenException, UserNotFoundException, NoSessionJwtException
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_access_token(request: Request) -> str:
    """Извлекаем access_token из кук."""
    token = request.cookies.get('user_access_token')
    if not token:
        raise TokenNoFound
    return token


def get_refresh_token(request: Request) -> str:
    """Извлекаем refresh_token из кук."""
    token = request.cookies.get('user_refresh_token')
    if not token:
        raise TokenNoFound
    return token


async def check_refresh_token(
        token: str = Depends(get_refresh_token),
        session: AsyncSession = Depends(get_session_without_commit),
) -> User:
    """ Проверяем refresh_token и возвращаем пользователя."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise NoJwtException

        user = await UsersDAO(session).find_one_or_none_by_id(data_id=int(user_id))
        if not user:
            raise NoJwtException

        return user
    except JWTError:
        raise NoJwtException


def get_session_id(request: Request) -> str:
    user_agent = request.headers.get("User-Agent")
    ip = request.client.host
    
    logger.info(f"User-Agent: {user_agent}, IP: {ip}")
    
    raw = f"{user_agent}-{ip}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db_session: AsyncSession = Depends(get_session_without_commit),
        session_id: str = Depends(get_session_id),
        token_type: str = "access",
) -> User:
    """Проверяем access_token и возвращаем пользователя."""
    logger.info(f"Session ID: {session_id}")
    
    try:
        # Декодируем токен
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise TokenExpiredException
    except JWTError:
        # Общая ошибка для токенов
        raise NoJwtException

    expire: str = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise TokenExpiredException

    user_id: str = payload.get('sub')
    if not user_id:
        raise NoUserIdException
    
    if not verify_token(token, user_id, token_type, session_id):
        raise NoSessionJwtException

    user = await UsersDAO(db_session).find_one_or_none_by_id(data_id=int(user_id))
    if not user:
        raise UserNotFoundException
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Проверяем права пользователя как администратора."""
    if current_user.role_id > 2:
        return current_user
    raise ForbiddenException


async def get_current_superadmin_user(current_user: User = Depends(get_current_user)) -> User:
    """Проверяем права пользователя как администратора."""
    if current_user.role_id == 4:
        return current_user
    raise ForbiddenException

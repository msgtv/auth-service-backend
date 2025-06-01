from typing import List, Annotated
from fastapi import APIRouter, Response, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.dao import UsersDAO
from app.auth.utils import (
    password_service, 
    token_service,
)
from app.exceptions import (
    UserAlreadyExistsException, 
    IncorrectEmailOrPasswordException,
)
from app.auth.schemas import (
    SUserRegister, 
    UsernameModel, 
    SUserAddDB, 
    SUserInfo, 
    STokens, 
    SRefreshToken,
)
from app.auth.dependencies import (
    get_current_user, 
    get_current_admin_user, 
    get_client_fingerprint,
)
from app.dao.dependencies import (
    get_session_with_commit, 
    get_session_without_commit,
)

router = APIRouter()


@router.post("/register")
async def register_user(
        user_data: SUserRegister,
        db_session: AsyncSession = Depends(get_session_with_commit)
) -> dict:
    """
    Регистрация нового пользователя

    Args:
        user_data: Данные для регистрации
        db_session: Сессия базы данных
    """
    # Проверка существования пользователя
    user_dao = UsersDAO(db_session)

    existing_user = await user_dao.find_one_or_none(
        filters=UsernameModel(username=user_data.username)
    )

    if existing_user:
        raise UserAlreadyExistsException()

    # Подготовка данных для добавления
    user_data_dict = user_data.model_dump()
    user_data_dict.pop('confirm_password', None)

    # Добавление пользователя
    await user_dao.add(values=SUserAddDB(**user_data_dict))

    return {'message': 'Вы успешно зарегистрированы!'}


@router.post("/token")
async def get_tokens(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db_session: AsyncSession = Depends(get_session_without_commit),
        client_fingerprint: str = Depends(get_client_fingerprint),
) -> STokens:
    """
    Получаем токены для пользователя

    Args:
        form_data: Данные для авторизации
        db_session: Сессия базы данных
        client_fingerprint: Уникальный идентификатор клиента
    """
    users_dao = UsersDAO(db_session)
    user = await users_dao.find_one_or_none(
        filters=UsernameModel(username=form_data.username)
    )

    if not (user and password_service.authenticate_user(user=user, password=form_data.password)):
        raise IncorrectEmailOrPasswordException(
            headers={'WWW-Authenticate': 'Bearer'},
        )
        
    tokens = await token_service.create_tokens(
            data={"sub": str(user.id)},
            client_fingerprint=client_fingerprint,
        )

    return STokens(
        **tokens
    )


@router.post("/logout")
async def logout(
        request: Request,
        user: User = Depends(get_current_user),
):
    """
    Выход из системы

    Args:
        response: Ответ
    """
    
    await token_service.invalidate_token_pair(
        user_id=user.id,
        client_fingerprint=get_client_fingerprint(request),
    )
    
    return {'message': 'Пользователь успешно вышел из системы'}


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)) -> SUserInfo:
    """
    Получаем информацию о текущем пользователе

    Args:
        user_data: Данные о пользователе
    """
    return user


@router.get(
    "/all_users",
    dependencies=[Depends(get_current_admin_user)],
)
async def get_all_users(
        db_session: AsyncSession = Depends(get_session_without_commit)
) -> List[SUserInfo]:
    """
    Получаем всех пользователей

    Args:
        db_session: Сессия базы данных
    """
    return await UsersDAO(db_session).find_all()


@router.post("/refresh")
async def process_refresh_token(
        db_session: Annotated[AsyncSession, Depends(get_session_without_commit)],
        refresh_token: SRefreshToken,
        request: Request,
) -> STokens:
    """
    Обновляем токены для пользователя

    Args:
        db_session: Сессия базы данных
        refresh_token: Токен для обновления
        request: Запрос
    """
    client_fingerprint = get_client_fingerprint(request)
    user = await get_current_user(
        token=refresh_token.refresh_token,
        db_session=db_session,
        token_type="refresh",
        client_fingerprint=client_fingerprint
    )
    
    tokens = await token_service.create_tokens(
        data={"sub": str(user.id)},
        client_fingerprint=client_fingerprint,
    )

    return STokens(
        **tokens
    )

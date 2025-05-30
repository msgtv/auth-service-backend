from typing import List, Annotated
from fastapi import APIRouter, Response, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils import authenticate_user, create_tokens
from app.dependencies.auth_dep import get_current_user, get_current_admin_user, check_refresh_token, get_session_id
from app.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from app.auth.dao import UsersDAO
from app.auth.schemas import SUserRegister, UsernameModel, SUserAddDB, SUserInfo, STokens, SRefreshToken

router = APIRouter()


@router.post("/register")
async def register_user(
        user_data: SUserRegister,
        db_session: AsyncSession = Depends(get_session_with_commit)
) -> dict:
    # Проверка существования пользователя
    user_dao = UsersDAO(db_session)

    existing_user = await user_dao.find_one_or_none(
        filters=UsernameModel(username=user_data.username)
    )

    if existing_user:
        raise UserAlreadyExistsException

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
        session_id: str = Depends(get_session_id),
) -> STokens:
    users_dao = UsersDAO(db_session)
    user = await users_dao.find_one_or_none(
        filters=UsernameModel(username=form_data.username)
    )

    if not (user and await authenticate_user(user=user, password=form_data.password)):
        raise IncorrectEmailOrPasswordException(
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    # TODO: Сохранить токены в базу данных или кэш Redis
    
    logger.info(f"Session ID: {session_id}")

    return STokens(**create_tokens(data={"sub": str(user.id)}, session_id=session_id))


@router.post("/logout")
async def logout(response: Response):
    # TODO: Удалить токены из базы данных или кэша Redis
    return {'message': 'Пользователь успешно вышел из системы'}


@router.get("/me")
async def get_me(user_data: User = Depends(get_current_user)) -> SUserInfo:
    return SUserInfo.model_validate(user_data)


@router.get(
    "/all_users",
    dependencies=[Depends(get_current_admin_user)],
)
async def get_all_users(
        db_session: AsyncSession = Depends(get_session_without_commit)
) -> List[SUserInfo]:
    return await UsersDAO(db_session).find_all()


@router.post("/refresh")
async def process_refresh_token(
        db_session: Annotated[AsyncSession, Depends(get_session_without_commit)],
        refresh_token: SRefreshToken,
        request: Request,
) -> STokens:
    session_id = get_session_id(request)
    user = await get_current_user(
        token=refresh_token.refresh_token,
        db_session=db_session,
        token_type="refresh",
        session_id=session_id
    )

    return STokens(**create_tokens(data={"sub": str(user.id)}, session_id=session_id))

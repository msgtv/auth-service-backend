from typing import List
from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils import authenticate_user, set_tokens
from app.dependencies.auth_dep import get_current_user, get_current_admin_user, check_refresh_token
from app.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from app.auth.dao import UsersDAO
from app.auth.schemas import SUserRegister, SUserAuth, UsernameModel, SUserAddDB, SUserInfo

router = APIRouter()


@router.post("/register/")
async def register_user(user_data: SUserRegister,
                        session: AsyncSession = Depends(get_session_with_commit)) -> dict:
    # Проверка существования пользователя
    user_dao = UsersDAO(session)

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


@router.post("/login/")
async def auth_user(
        response: Response,
        user_data: SUserAuth,
        session: AsyncSession = Depends(get_session_without_commit)
) -> dict:
    users_dao = UsersDAO(session)
    user = await users_dao.find_one_or_none(
        filters=UsernameModel(username=user_data.username)
    )

    if not (user and await authenticate_user(user=user, password=user_data.password)):
        raise IncorrectEmailOrPasswordException
    set_tokens(response, user.id)
    return {
        'ok': True,
        'message': 'Авторизация успешна!'
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("user_access_token")
    response.delete_cookie("user_refresh_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)) -> SUserInfo:
    return SUserInfo.model_validate(user_data)


@router.get(
    "/all_users/",
    dependencies=[Depends(get_current_admin_user)],
)
async def get_all_users(
        session: AsyncSession = Depends(get_session_with_commit)
) -> List[SUserInfo]:
    return await UsersDAO(session).find_all()


@router.post("/refresh")
async def process_refresh_token(
        response: Response,
        user: User = Depends(check_refresh_token)
):
    set_tokens(response, user.id)
    return {"message": "Токены успешно обновлены"}

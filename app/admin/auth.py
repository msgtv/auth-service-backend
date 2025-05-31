from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.auth.dao import UsersDAO
from app.auth.models import User
from app.auth.schemas import UsernameModel
from app.auth.utils import token_service
from app.config import settings
from app.dao.database import async_session_maker
from app.auth.dependencies import get_current_admin_user, get_current_user, check_refresh_token, get_client_fingerprint
from app.exceptions import TokenExpiredException


class AdminAuth(AuthenticationBackend):
    """Аутентификация администратора для SQLAdmin"""
    
    async def login(self, request: Request) -> bool:
        """
        Аутентификация администратора для SQLAdmin
        
        Args:
            request: Запрос
        """
        form = await request.form()
        username, password = form.get('username'), form.get('password')

        async with async_session_maker() as session:
            user: User = await UsersDAO(session).find_one_or_none(
                filters=UsernameModel(username=username)
            )

        if user:
            request.session.update(
                token_service.create_tokens(
                    data={"sub": str(user.id)},
                    client_fingerprint=get_client_fingerprint(request),
                )
            )

        return True

    async def logout(self, request: Request) -> bool:
        """
        Выход из системы для SQLAdmin
        Очищает сессию и инвалидирует пару токенов пользователя
        Перенаправляет на страницу входа
                
        Args:
            request: Запрос
        """
        access_token = request.session.get('access_token')
        
        request.session.clear()
        
        client_fingerprint = get_client_fingerprint(request)
        
        payload = token_service.decode_token(access_token)
        
        user_id = payload.get('sub')
        if not user_id:
            return RedirectResponse(request.url_for('admin:login'), status_code=302)
        
        token_service.invalidate_token_pair(
            user_id=user_id,
            client_fingerprint=client_fingerprint,
        )
        
        return RedirectResponse(request.url_for('admin:login'), status_code=302)

    async def authenticate(self, request: Request) -> bool|RedirectResponse:
        """        
        Проверяет аутентификацию пользователя для доступа к админ-панели SQLAdmin.
        
        Процесс аутентификации:
        1. Проверяет наличие access_token в сессии
        2. Если токен отсутствует - перенаправляет на страницу входа
        3. Проверяет валидность access_token и получает пользователя
        4. При истечении access_token пытается обновить токены через refresh_token
        5. Проверяет наличие прав супер администратора у пользователя
        6. При отсутствии прав перенаправляет на страницу входа
        
        Args:
            request: Запрос
        """
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')

        if not access_token:
            return RedirectResponse(request.url_for('admin:login'), status_code=302)

        async with async_session_maker() as session:
            try:
                user = await get_current_user(token=access_token, session=session)
            except TokenExpiredException:
                user = check_refresh_token(token=refresh_token, session=session)
                request.session.update(
                    token_service.create_tokens(
                        data={'sub': str(user.id)},
                        client_fingerprint=get_client_fingerprint(request),
                    )
                )

            if not user:
                return RedirectResponse(request.url_for('admin:login'), status_code=302)

            admin_user = await get_current_admin_user(user)

            if not admin_user:
                return RedirectResponse(request.url_for('admin:login'), status_code=302)

        return True

authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)

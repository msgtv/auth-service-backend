from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.auth.dao import UsersDAO
from app.auth.models import User
from app.auth.schemas import UsernameModel
from app.auth.utils import create_tokens
from app.config import settings
from app.dependencies.auth_dep import get_current_admin_user, get_current_user, check_refresh_token
from app.dependencies.dao_dep import get_session_without_commit
from app.exceptions import TokenExpiredException


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get('username'), form.get('password')

        async with get_session_without_commit() as session:
            user: User = await UsersDAO(session).find_one_or_none(
                filters=UsernameModel(username=username)
            )

        if user:
            request.session.update(create_tokens(data={"sub": str(user.id)}))

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool|RedirectResponse:
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')

        if not access_token:
            return RedirectResponse(request.url_for('admin:login'), status_code=302)

        async with get_session_without_commit() as session:
            try:
                user = await get_current_user(token=access_token, session=session)
            except TokenExpiredException:
                user = check_refresh_token(token=refresh_token, session=session)
                request.session.update(create_tokens(data={'sub': str(user.id)}))

            if not user:
                return RedirectResponse(request.url_for('admin:login'), status_code=302)

            admin_user = await get_current_admin_user(user)

            if not admin_user:
                return RedirectResponse(request.url_for('admin:login'), status_code=302)

        return True

authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)

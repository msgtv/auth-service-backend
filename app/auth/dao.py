from app.dao.base import BaseDAO
from app.auth.models import User, Role


class UsersDAO(BaseDAO):
    """DAO для работы с пользователями"""
    model = User


class RoleDAO(BaseDAO):
    """DAO для работы с ролями"""
    model = Role

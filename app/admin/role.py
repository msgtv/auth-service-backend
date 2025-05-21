from sqladmin import ModelView

from app.auth.models import Role


class RoleAdmin(ModelView, model=Role):
    name = 'Роль'
    name_plural = 'Роли'
    icon = 'fa-solid fa-shield-halved'

    column_list = [
        'id',
        'name',
    ]



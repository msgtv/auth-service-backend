from sqladmin import ModelView

from app.auth.models import User

class UserAdmin(ModelView, model=User):
    name = 'Пользователь'
    name_plural = 'Пользователи'

    icon = 'fa-solid fa-user'

    column_list = [
        'id',
        'username',
        'first_name',
        'last_name',
    ]

    column_details_exclude_list = [
        'password',
    ]

    can_delete = False

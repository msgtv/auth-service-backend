import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.auth.dao import UsersDAO
from app.auth.schemas import UsernameModel


@pytest.mark.parametrize(
    "username,role_id,is_present",
    [
        ('defaultuser', 1, True),
        ('admin', 3, True),
        ('manager', 2, True),
        ('superadmin', 4, True),
        ('superadmin', 2, False),
    ]
)
async def test_get_user_by_username(
        username,
        role_id,
        is_present,
        session: AsyncSession,
):
    user_dao = UsersDAO(session)

    user = await user_dao.find_one_or_none(UsernameModel(username=username))

    if is_present:
        assert user.username == username
        assert user.role_id == role_id
    else:
        assert not user

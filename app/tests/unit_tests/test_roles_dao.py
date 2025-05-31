import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.auth.dao import RoleDAO
from app.auth.schemas import RoleModel


@pytest.mark.parametrize(
    "role_id,name,is_present",
    [
        (1, 'default', True),
        (2, 'manager', True),
        (3, 'admin', True),
        (4, 'root', True),
        (5, 'default', False),
        (3, 'manager', False),
        (4, 'default', False),
    ]
)
async def test_get_role_by_id(
        role_id,
        name,
        is_present,
        session: AsyncSession,
):
    role_dao = RoleDAO(session)

    role = await role_dao.find_one_or_none(RoleModel(id=role_id, name=name))

    if is_present:
        assert role.id == role_id
        assert role.name == name
    else:
        assert not role

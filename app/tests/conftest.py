import json
from datetime import datetime

import pytest
from sqlalchemy import insert
from httpx import AsyncClient, ASGITransport

from app.main import app as fastapi_app
from app.config import settings
from app.dao.database import Base, async_session_maker, engine
from app.auth.models import Role, User


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    assert settings.MODE == 'TEST'

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    def open_mock_json(model: str):
        with open(f"app/tests/mock_{model}.json", encoding='utf-8') as f:
            return json.load(f)

    users = open_mock_json('users')
    roles = open_mock_json('roles')

    async with async_session_maker() as s:
        add_roles = insert(Role).values(roles)
        add_users = insert(User).values(users)

        await s.execute(add_roles)
        await s.execute(add_users)

        await s.commit()


@pytest.fixture(scope='function')
async def ac():
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test/",
    ) as client:
        yield client


@pytest.fixture(scope='session')
async def client_tokens():
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test/",
    ) as ac:
        email = "teststests"
        passw = "teststests"

        await ac.post(
            "/auth/register",
            json={
                "email": email,
                "password": passw,
                "confirm_password": passw,
            }
        )

        res = await ac.post(
            "/auth/token",
            data={
                "username": email,
                "password": passw,
            }
        )

        assert res.status_code == 200

        tokens = await res.json()

        assert tokens.get('access_token')
        assert tokens.get('refresh_token')

    return tokens

@pytest.fixture(scope='function')
async def session():
    async with async_session_maker() as session:
        yield session

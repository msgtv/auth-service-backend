import json
from datetime import datetime

import pytest
import redis.asyncio as redis
from sqlalchemy import insert
from httpx import AsyncClient, ASGITransport

from app.auth.redis_manager import RedisTokenManager
from app.main import app as fastapi_app
from app.config import settings
from app.dao.database import Base, async_session_maker, engine
from app.auth.models import Role, User


@pytest.fixture(autouse=True, scope="module")
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


@pytest.fixture(scope='function')
async def client_tokens():
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test/",
    ) as ac:
        res = await ac.post(
            "/auth/token",
            data={
                "username": 'defaultuser',
                "password": 'defaultuser',
            }
        )

        assert res.status_code == 200

        tokens = res.json()

        assert tokens.get('access_token')
        assert tokens.get('refresh_token')

    return tokens


@pytest.fixture(scope='module')
async def session():
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope='module')
async def redis_client():
    assert settings.MODE == 'TEST'
    
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=1,  # Using different DB for tests
        decode_responses=True
    )
    
    try:
        yield client
    finally:
        await client.flushdb()  # Clean up after tests
        await client.aclose()


@pytest.fixture(scope='module')
def redis_token_manager(redis_client):
    """Фикстура для создания RedisTokenManager с тестовым Redis-клиентом""" 
    manager = RedisTokenManager()
    manager.redis_client = redis_client
    return manager


@pytest.fixture(autouse=True, scope="module")
async def clean_redis(redis_client):
    try:
        yield
    finally:
        await redis_client.flushdb()  # Clean Redis after each test

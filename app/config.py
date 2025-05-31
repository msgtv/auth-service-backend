from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MODE: Literal['DEV', 'TEST', 'PROD'] = 'DEV'

    SECRET_KEY: str
    ALGORITHM: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    TEST_POSTGRES_USER: str
    TEST_POSTGRES_PASSWORD: str
    TEST_POSTGRES_DB: str
    TEST_POSTGRES_HOST: str
    TEST_POSTGRES_PORT: int

    # Redis settings
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str | None
    
    TEST_REDIS_HOST: str
    TEST_REDIS_PORT: int
    TEST_REDIS_DB: int
    TEST_REDIS_PASSWORD: str | None

    model_config = SettingsConfigDict(env_file=".env")


# Получаем параметры для загрузки переменных среды
settings = Settings()

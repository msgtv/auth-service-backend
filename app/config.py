from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
    TEST_POSTGRES_HOST: str
    TEST_POSTGRES_PORT: int
    TEST_POSTGRES_DB: str

    model_config = SettingsConfigDict(env_file=f".env")


# Получаем параметры для загрузки переменных среды
settings = Settings()

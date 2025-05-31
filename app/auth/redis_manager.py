from datetime import timedelta

from redis import Redis

from app.config import settings


class RedisTokenManager:
    """Класс для работы с Redis"""

    access_token_prefix = "access"
    refresh_token_prefix = "refresh"
    
    def __init__(self):
        self.redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
    
    def _get_token_key(
            self,
            subject: int | str,
            token_type: str,
            client_fingerprint: str,
    ) -> str:
        """Получить ключ для токена"""
        return f"{token_type}:{subject}:{client_fingerprint}"

    def _get_user_tokens(
            self,
            subject: int | str,
    ) -> list[str]:
        """Получить все токены для пользователя"""
        tokens = []
        for token_type in (self.access_token_prefix, self.refresh_token_prefix):
            token_type_keys = self.redis_client.keys(f"{token_type}:{subject}:*")
            tokens.extend(token_type_keys)
        return tokens

    def store_token(
            self,
            subject: int | str,
            token: str,
            token_type: str,
            expire_time: int,
            client_fingerprint: str,
    ):
        """Сохранить токен в Redis с истечением времени"""
        key = self._get_token_key(subject, token_type, client_fingerprint)
        self.redis_client.set(key, token, ex=expire_time)

    def get_token(
            self,
            subject: int | str,
            token_type: str,
            client_fingerprint: str,
    ) -> str | None:
        """Получить токен из Redis"""
        key = self._get_token_key(subject, token_type, client_fingerprint)
        return self.redis_client.get(key)

    def invalidate_token(
            self,
            subject: int | str,
            token_type: str,
            client_fingerprint: str,
    ):
        """Удалить токен из Redis"""
        key = self._get_token_key(subject, token_type, client_fingerprint)
        self.redis_client.delete(key)
    
    def invalidate_token_pair(
            self,
            subject: int | str,
            client_fingerprint: str,
    ):
        """Удалить пару токенов из Redis"""
        for token_type in (self.access_token_prefix, self.refresh_token_prefix):
            self.invalidate_token(subject, token_type, client_fingerprint)

    def invalidate_all_user_tokens(
            self,
            subject: int | str,
    ):
        """Удалить все токены для пользователя на всех устройствах"""
        for k in self._get_user_tokens(subject):
            self.redis_client.delete(k)

    def is_token_verified(
            self,
            subject: int | str,
            token_type: str,
            token: str,
            client_fingerprint: str,
    ) -> bool:
        """Проверить, является ли токен черным списком"""
        stored_token = self.get_token(subject, token_type, client_fingerprint)
        return stored_token == token
 
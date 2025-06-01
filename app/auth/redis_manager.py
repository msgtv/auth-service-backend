from redis.asyncio import Redis

from app.dao.database import REDIS_URL


class RedisTokenManager:
    """Класс для работы с Redis"""

    access_token_prefix = "access"
    refresh_token_prefix = "refresh"
    
    def __init__(self):
        self.redis_client = Redis.from_url(
            url=REDIS_URL,
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

    async def _get_user_tokens(
            self,
            subject: int | str,
    ) -> list[str]:
        """Получить все токены для пользователя"""
        tokens = []
        for token_type in (self.access_token_prefix, self.refresh_token_prefix):
            token_type_keys = await self.redis_client.keys(f"{token_type}:{subject}:*")
            tokens.extend(token_type_keys)
        return tokens

    async def store_token(
            self,
            subject: int | str,
            token: str,
            token_type: str,
            expire_time: int,
            client_fingerprint: str,
    ):
        """Сохранить токен в Redis с истечением времени"""
        key = self._get_token_key(subject, token_type, client_fingerprint)
        await self.redis_client.set(key, token, ex=expire_time)

    async def get_token(
            self,
            subject: int | str,
            token_type: str,
            client_fingerprint: str,
    ) -> str | None:
        """Получить токен из Redis"""
        key = self._get_token_key(subject, token_type, client_fingerprint)
        return await self.redis_client.get(key)

    async def invalidate_token(
            self,
            subject: int | str,
            token_type: str,
            client_fingerprint: str,
    ):
        """Удалить токен из Redis"""
        key = self._get_token_key(subject, token_type, client_fingerprint)
        await self.redis_client.delete(key)
    
    async def invalidate_token_pair(
            self,
            subject: int | str,
            client_fingerprint: str,
    ):
        """Удалить пару токенов из Redis"""
        for token_type in (self.access_token_prefix, self.refresh_token_prefix):
            await self.invalidate_token(subject, token_type, client_fingerprint)

    async def invalidate_all_user_tokens(
            self,
            subject: int | str,
    ):
        """Удалить все токены для пользователя на всех устройствах"""
        for k in await self._get_user_tokens(subject):
            await self.redis_client.delete(k)

    async def is_token_verified(
            self,
            subject: int | str,
            token_type: str,
            token: str,
            client_fingerprint: str,
    ) -> bool:
        """Проверить, является ли токен черным списком"""
        stored_token = await self.get_token(subject, token_type, client_fingerprint)
        
        return stored_token == token
 
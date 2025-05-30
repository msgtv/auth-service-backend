from datetime import timedelta

from redis import Redis

from app.config import settings


class RedisTokenManager:
    def __init__(self):
        self.redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
    
    def _get_token_key(self, subject: int | str, token_type: str, session_id: str) -> str:
        return f"{token_type}:{subject}:{session_id}"

    def store_token(self, subject: int | str, token: str, token_type: str, expire_time: int, session_id: str):
        """Store token in Redis with expiration"""
        key = self._get_token_key(subject, token_type, session_id)
        self.redis_client.set(key, token, ex=expire_time)

    def get_token(self, subject: int | str, token_type: str, session_id: str) -> str | None:
        """Get token from Redis"""
        key = self._get_token_key(subject, token_type, session_id)
        return self.redis_client.get(key)

    def invalidate_session_tokens(self, subject: int | str, token_type: str, session_id: str):
        """Invalidate token by removing it from Redis"""
        key = self._get_token_key(subject, token_type, session_id)
        self.redis_client.delete(key)

    def invalidate_all_user_tokens(self, subject: int | str, session_id: str):
        """Invalidate all tokens for a user"""
        # TODO: Удалить все токены для пользователя на всех устройствах
        for token_type in ["access", "refresh"]:
            self.invalidate_token(subject, token_type, session_id)

    def is_token_verified(self, subject: int | str, token_type: str, token: str, session_id: str) -> bool:
        """Check if token is blacklisted by comparing with stored token"""
        stored_token = self.get_token(subject, token_type, session_id)
        return stored_token == token


# Create a global instance
redis_manager = RedisTokenManager() 
from fastapi import status, HTTPException

# Пользователь уже существует
class UserAlreadyExistsException(HTTPException):
    status_code = status.HTTP_409_CONFLICT
    detail = 'Пользователь уже существует'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

# Пользователь не найден
class UserNotFoundException(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = 'Пользователь не найден'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

# Отсутствует идентификатор пользователя
class UserIdNotFoundException(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = 'Отсутствует идентификатор пользователя'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

# Неверная почта или пароль
class IncorrectEmailOrPasswordException(HTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = 'Неверные имя пользователя или пароль'

    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

# Токен истек
class TokenExpiredException(HTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = 'Токен истек'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

# Некорректный формат токена
class InvalidTokenFormatException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = 'Некорректный формат токена'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )


# Токен отсутствует в заголовке
class TokenNoFound(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = 'Токен отсутствует в заголовке'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

# Невалидный JWT токен
class NoJwtException(HTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = 'Токен не валидный'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

# Не найден ID пользователя
class NoUserIdException(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = 'Не найден ID пользователя'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

# Не найден ID сессии
class NoSessionJwtException(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = 'Токен не привязан к сессии'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

# Недостаточно прав
class ForbiddenException(HTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = 'Недостаточно прав'
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )

class TokenInvalidFormatException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Неверный формат токена. Ожидается 'Bearer <токен>'"
    
    def __init__(self, headers: dict[str, str | int] = None):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers=headers,
        )
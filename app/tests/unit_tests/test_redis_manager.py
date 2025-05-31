async def test_store_and_get_token(redis_token_manager):
    """Тест сохранения и получения токена"""
    # Тестовые данные
    subject = 123
    token = "test_token_123"
    token_type = "access"
    expire_time = 300
    fingerprint = "test_device"

    # Сохраняем токен
    await redis_token_manager.store_token(
        subject=subject,
        token=token,
        token_type=token_type,
        expire_time=expire_time,
        client_fingerprint=fingerprint
    )

    # Получаем токен
    stored_token = await redis_token_manager.get_token(
        subject=subject,
        token_type=token_type,
        client_fingerprint=fingerprint
    )

    assert stored_token == token


async def test_invalidate_token(redis_token_manager):
    """Тест инвалидации токена"""
    # Сохраняем токен
    subject = 456
    token = "test_token_456"
    token_type = "refresh"
    fingerprint = "test_device"

    await redis_token_manager.store_token(
        subject=subject,
        token=token,
        token_type=token_type,
        expire_time=300,
        client_fingerprint=fingerprint
    )

    # Инвалидируем токен
    await redis_token_manager.invalidate_token(
        subject=subject,
        token_type=token_type,
        client_fingerprint=fingerprint
    )

    # Проверяем что токен удален
    stored_token = await redis_token_manager.get_token(
        subject=subject,
        token_type=token_type,
        client_fingerprint=fingerprint
    )
    assert stored_token is None


async def test_invalidate_token_pair(redis_token_manager):
    """Тест инвалидации пары токенов"""
    subject = 789
    fingerprint = "test_device"
    
    # Сохраняем пару токенов
    tokens = {
        "access": "access_token_789",
        "refresh": "refresh_token_789"
    }
    
    for token_type, token in tokens.items():
        await redis_token_manager.store_token(
            subject=subject,
            token=token,
            token_type=token_type,
            expire_time=300,
            client_fingerprint=fingerprint
        )

    # Инвалидируем пару токенов
    await redis_token_manager.invalidate_token_pair(
        subject=subject,
        client_fingerprint=fingerprint
    )

    # Проверяем что оба токена удалены
    for token_type in tokens.keys():
        stored_token = await redis_token_manager.get_token(
            subject=subject,
            token_type=token_type,
            client_fingerprint=fingerprint
        )
        assert stored_token is None


async def test_invalidate_all_user_tokens(redis_token_manager):
    """Тест инвалидации всех токенов пользователя"""
    subject = 999
    devices = ["device1", "device2", "device3"]
    
    # Сохраняем токены для разных устройств
    for device in devices:
        for token_type in ["access", "refresh"]:
            await redis_token_manager.store_token(
                subject=subject,
                token=f"{token_type}_token_{device}",
                token_type=token_type,
                expire_time=300,
                client_fingerprint=device
            )

    # Инвалидируем все токены пользователя
    await redis_token_manager.invalidate_all_user_tokens(subject)

    # Проверяем что все токены удалены
    for device in devices:
        for token_type in ["access", "refresh"]:
            stored_token = await redis_token_manager.get_token(
                subject=subject,
                token_type=token_type,
                client_fingerprint=device
            )
            assert stored_token is None


async def test_is_token_verified(redis_token_manager):
    """Тест проверки валидности токена"""
    subject = 111
    token = "test_token_111"
    token_type = "access"
    fingerprint = "test_device"

    # Сохраняем токен
    await redis_token_manager.store_token(
        subject=subject,
        token=token,
        token_type=token_type,
        expire_time=300,
        client_fingerprint=fingerprint
    )

    # Проверяем правильный токен
    assert await redis_token_manager.is_token_verified(
        subject=subject,
        token_type=token_type,
        token=token,
        client_fingerprint=fingerprint
    )

    # Проверяем неправильный токен
    assert not await redis_token_manager.is_token_verified(
        subject=subject,
        token_type=token_type,
        token="wrong_token",
        client_fingerprint=fingerprint
    ) 
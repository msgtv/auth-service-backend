async def test_redis_connection(redis_client):
    # Test that we can connect to Redis
    assert await redis_client.ping()


async def test_redis_operations(redis_client):
    # Test basic Redis operations
    await redis_client.set("test_key", "test_value")
    value = await redis_client.get("test_key")
    assert value == "test_value"


async def test_redis_cleanup(redis_client):
    # Test that cleanup works between tests
    result = await redis_client.get("test_key_none")
    
    assert result is None  # Previous test data should be cleaned


async def test_redis_hash_operations(redis_client):
    # Test hash operations
    test_hash = {
        "field1": "value1",
        "field2": "value2"
    }
    await redis_client.hset("test_hash", mapping=test_hash)
    
    # Test getting single field
    assert await redis_client.hget("test_hash", "field1") == "value1"
    
    # Test getting all fields
    stored_hash = await redis_client.hgetall("test_hash")
    assert stored_hash == test_hash


async def test_redis_list_operations(redis_client):
    # Test list operations
    test_list = ["item1", "item2", "item3"]
    
    # Add items to list
    await redis_client.rpush("test_list", *test_list)
    
    # Test list length
    assert await redis_client.llen("test_list") == len(test_list)
    
    # Test getting all items
    stored_list = await redis_client.lrange("test_list", 0, -1)
    assert stored_list == test_list 
# app/config/redis.py

import redis.asyncio as redis

from app.config.settings import settings


# =========================================================
# REDIS CLIENT
# =========================================================
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


# =========================================================
# INIT REDIS
# =========================================================
async def init_redis():

    try:
        await redis_client.ping()
        print("Redis connected successfully")

    except Exception as e:
        print(f"Redis connection failed: {e}")
        raise e


# =========================================================
# GET REDIS CLIENT
# =========================================================
async def get_redis():
    return redis_client


# =========================================================
# BASIC CACHE HELPERS
# =========================================================
async def set_cache(
    key: str,
    value: str,
    expire: int = 3600
):
    await redis_client.set(
        key,
        value,
        ex=expire
    )


async def get_cache(
    key: str
):
    return await redis_client.get(key)


async def delete_cache(
    key: str
):
    await redis_client.delete(key)


# =========================================================
# USER CONCURRENCY CONTROL
# =========================================================
async def increment_user_requests(user_id: int):

    key = f"user:{user_id}:active_requests"

    current = await redis_client.incr(key)

    await redis_client.expire(key, 300)

    return current


async def decrement_user_requests(user_id: int):

    key = f"user:{user_id}:active_requests"

    current = await redis_client.decr(key)

    if current <= 0:
        await redis_client.delete(key)

    return current


async def get_user_active_requests(user_id: int):

    key = f"user:{user_id}:active_requests"

    value = await redis_client.get(key)

    return int(value or 0)


# =========================================================
# AI MEMORY CACHE
# =========================================================
async def cache_conversation_context(
    conversation_id: str,
    context: str,
    expire: int = 86400
):

    key = f"conversation:{conversation_id}:context"

    await redis_client.set(
        key,
        context,
        ex=expire
    )


async def get_conversation_context(
    conversation_id: str
):

    key = f"conversation:{conversation_id}:context"

    return await redis_client.get(key)
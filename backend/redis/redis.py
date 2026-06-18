import os
import json

from typing import Any

import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

class RedisManager:
    @staticmethod
    def set(key: str, value: Any, expire: int | None = None):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        redis_client.set(key, value, ex=expire)

    @staticmethod
    def get(key: str):
        value = redis_client.get(key)

        if not value:
            return None

        try:
            return json.loads(value)

        except Exception:
            return value

    @staticmethod
    def delete(key: str):
        redis_client.delete(key)

    @staticmethod
    def exists(key: str):
        return redis_client.exists(key)

    @staticmethod
    def expire(key: str, seconds: int):
        redis_client.expire(key, seconds)

    @staticmethod
    def increment(key: str, amount: int = 1):
        return redis_client.incr(key, amount)

    @staticmethod
    def push_list(key: str, value: Any):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        redis_client.rpush(key, value)

    @staticmethod
    def get_list(key: str):
        values = redis_client.lrange(key,0, -1)

        result = []

        for value in values:
            try:
                result.append(
                    json.loads(value)
                )

            except Exception:
                result.append(value)

        return result

if __name__ == '__main__':
    pass
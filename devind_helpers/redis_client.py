"""Модуль создания подключения к редису."""

import os
from typing import Optional

from redis import Redis

__all__ = ('redis',)


try:
    redis: Optional[Redis] = Redis(
        host=os.getenv('REDIS_SERVER', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0))
    )
    redis.ping()
except ConnectionError:
    redis: Optional[Redis] = None

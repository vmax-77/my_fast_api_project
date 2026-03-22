import redis
from app.config import settings
import os

if os.environ.get("PYTEST_RUNNING"):
    class DummyRedis:
        def get(self, key):
            return None
        def setex(self, key, time, value):
            pass
        def delete(self, key):
            pass
        def flushall(self):
            pass
    redis_client = DummyRedis()
else:
    import redis
    from app.config import settings
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
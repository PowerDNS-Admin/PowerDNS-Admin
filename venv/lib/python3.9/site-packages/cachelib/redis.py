import typing as _t
import warnings

from cachelib.base import BaseCache
from cachelib.serializers import RedisSerializer


class RedisCache(BaseCache):
    """Uses the Redis key-value store as a cache backend.

    The first argument can be either a string denoting address of the Redis
    server or an object resembling an instance of a redis.Redis class.

    Note: Python Redis API already takes care of encoding unicode strings on
    the fly.

    :param host: address of the Redis server or an object which API is
                 compatible with the official Python Redis client (redis-py).
    :param port: port number on which Redis server listens for connections.
    :param password: password authentication for the Redis server.
    :param db: db (zero-based numeric index) on Redis Server to connect.
    :param default_timeout: the default timeout that is used if no timeout is
                            specified on :meth:`~BaseCache.set`. A timeout of
                            0 indicates that the cache never expires.
    :param key_prefix: A prefix that should be added to all keys.

    Any additional keyword arguments will be passed to ``redis.Redis``.
    """

    serializer = RedisSerializer()

    def __init__(
        self,
        host: _t.Any = "localhost",
        port: int = 6379,
        password: _t.Optional[str] = None,
        db: int = 0,
        default_timeout: int = 300,
        key_prefix: _t.Optional[str] = None,
        **kwargs: _t.Any
    ):
        BaseCache.__init__(self, default_timeout)
        if host is None:
            raise ValueError("RedisCache host parameter may not be None")
        if isinstance(host, str):
            try:
                import redis
            except ImportError as err:
                raise RuntimeError("no redis module found") from err
            if kwargs.get("decode_responses", None):
                raise ValueError("decode_responses is not supported by RedisCache.")
            self._client = redis.Redis(
                host=host, port=port, password=password, db=db, **kwargs
            )
        else:
            self._client = host
        self.key_prefix = key_prefix or ""

    def _normalize_timeout(self, timeout: _t.Optional[int]) -> int:
        timeout = BaseCache._normalize_timeout(self, timeout)
        if timeout == 0:
            timeout = -1
        return timeout

    def dump_object(self, value: _t.Any) -> bytes:
        warnings.warn(
            "'dump_object' is deprecated and will be removed in the future."
            "This is a proxy call to 'RedisCache.serializer.dumps'",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.serializer.dumps(value)

    def load_object(self, value: _t.Any) -> _t.Any:
        warnings.warn(
            "'load_object' is deprecated and will be removed in the future."
            "This is a proxy call to 'RedisCache.serializer.loads'",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.serializer.loads(value)

    def get(self, key: str) -> _t.Any:
        return self.load_object(self._client.get(self.key_prefix + key))

    def get_many(self, *keys: str) -> _t.List[_t.Any]:
        if self.key_prefix:
            prefixed_keys = [self.key_prefix + key for key in keys]
        else:
            prefixed_keys = [k for k in keys]
        return [self.load_object(x) for x in self._client.mget(prefixed_keys)]

    def set(
        self, key: str, value: _t.Any, timeout: _t.Optional[int] = None
    ) -> _t.Optional[bool]:
        timeout = self._normalize_timeout(timeout)
        dump = self.dump_object(value)
        if timeout == -1:
            result = self._client.set(name=self.key_prefix + key, value=dump)
        else:
            result = self._client.setex(
                name=self.key_prefix + key, value=dump, time=timeout
            )
        return result

    def add(self, key: str, value: _t.Any, timeout: _t.Optional[int] = None) -> bool:
        timeout = self._normalize_timeout(timeout)
        dump = self.dump_object(value)
        return self._client.setnx(
            name=self.key_prefix + key, value=dump
        ) and self._client.expire(name=self.key_prefix + key, time=timeout)

    def set_many(
        self, mapping: _t.Dict[str, _t.Any], timeout: _t.Optional[int] = None
    ) -> _t.List[_t.Any]:
        timeout = self._normalize_timeout(timeout)
        # Use transaction=False to batch without calling redis MULTI
        # which is not supported by twemproxy
        pipe = self._client.pipeline(transaction=False)

        for key, value in mapping.items():
            dump = self.dump_object(value)
            if timeout == -1:
                pipe.set(name=self.key_prefix + key, value=dump)
            else:
                pipe.setex(name=self.key_prefix + key, value=dump, time=timeout)
        results = pipe.execute()
        return [k for k, was_set in zip(mapping.keys(), results) if was_set]

    def delete(self, key: str) -> bool:
        return bool(self._client.delete(self.key_prefix + key))

    def delete_many(self, *keys: str) -> _t.List[_t.Any]:
        if not keys:
            return []
        if self.key_prefix:
            prefixed_keys = [self.key_prefix + key for key in keys]
        else:
            prefixed_keys = [k for k in keys]
        self._client.delete(*prefixed_keys)
        return [k for k in prefixed_keys if not self.has(k)]

    def has(self, key: str) -> bool:
        return bool(self._client.exists(self.key_prefix + key))

    def clear(self) -> bool:
        status = 0
        if self.key_prefix:
            keys = self._client.keys(self.key_prefix + "*")
            if keys:
                status = self._client.delete(*keys)
        else:
            status = self._client.flushdb()
        return bool(status)

    def inc(self, key: str, delta: int = 1) -> _t.Optional[int]:
        return self._client.incr(name=self.key_prefix + key, amount=delta)

    def dec(self, key: str, delta: int = 1) -> _t.Optional[int]:
        return self._client.incr(name=self.key_prefix + key, amount=-delta)

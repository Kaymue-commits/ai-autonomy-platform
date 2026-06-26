"""
简单内存缓存 - 替代 Upstash Redis
支持 TTL (过期时间), 异步锁, 批量获取
仿 worldmonitor _shared/redis.ts
"""
import asyncio
import time
from typing import Any, Optional, Callable, Awaitable, Dict
from collections import OrderedDict
import threading


class TTLCache:
    """线程安全的 TTL 内存缓存 (LRU 淘汰)"""

    def __init__(self, max_size: int = 10000):
        self._cache: OrderedDict[str, tuple] = OrderedDict()  # key -> (value, expire_at)
        self._lock = threading.Lock()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值, 过期返回None"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            value, expire_at = self._cache[key]
            if expire_at > 0 and time.time() > expire_at:
                # 已过期
                del self._cache[key]
                self._misses += 1
                return None
            self._hits += 1
            # LRU: 移到末尾
            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value: Any, ttl_seconds: int = 600):
        """设置缓存, ttl_seconds=0表示永不过期"""
        with self._lock:
            expire_at = time.time() + ttl_seconds if ttl_seconds > 0 else 0
            self._cache[key] = (value, expire_at)
            self._cache.move_to_end(key)
            # LRU 淘汰
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        with self._lock:
            self._cache.clear()

    def stats(self) -> Dict[str, int]:
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / max(self._hits + self._misses, 1), 3),
            }


# 全局缓存实例
_cache = TTLCache(max_size=10000)


def cache_get(key: str) -> Optional[Any]:
    return _cache.get(key)


def cache_set(key: str, value: Any, ttl: int = 600):
    _cache.set(key, value, ttl)


def cache_delete(key: str) -> bool:
    return _cache.delete(key)


def cache_clear():
    _cache.clear()


def cache_stats() -> Dict:
    return _cache.stats()


async def cached_fetch(key: str, ttl: int, fetch_fn: Callable[[], Awaitable[Any]]) -> Optional[Any]:
    """
    缓存包装: 先查缓存, 没有则调用 fetch_fn 获取并存入缓存
    仿 worldmonitor cachedFetchJson<T>(key, ttl, () => fetcher())
    """
    cached = cache_get(key)
    if cached is not None:
        return cached

    try:
        value = await fetch_fn()
        if value is not None:
            cache_set(key, value, ttl)
        return value
    except Exception:
        return None


# ===== 单飞锁 (防止同一 key 同时穿透) =====
_locks: Dict[str, asyncio.Lock] = {}
_locks_meta_lock = asyncio.Lock()


async def get_lock(key: str) -> asyncio.Lock:
    """获取 key 对应的 asyncio.Lock (单飞)"""
    async with _locks_meta_lock:
        if key not in _locks:
            _locks[key] = asyncio.Lock()
        return _locks[key]


async def single_flight(key: str, ttl: int, fetch_fn: Callable[[], Awaitable[Any]]) -> Optional[Any]:
    """
    单飞缓存: 同一 key 并发请求只触发一次 fetch_fn
    仿世界监测器的单飞模式
    """
    cached = cache_get(key)
    if cached is not None:
        return cached

    lock = await get_lock(key)
    async with lock:
        # 双重检查 (lock 内再看一次缓存)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            value = await fetch_fn()
            if value is not None:
                cache_set(key, value, ttl)
            return value
        except Exception:
            return None


if __name__ == '__main__':
    import asyncio

    async def test():
        # 基本缓存
        cache_set("k1", "hello", ttl=2)
        print(f"get k1: {cache_get('k1')}")

        # TTL
        await asyncio.sleep(3)
        print(f"get k1 after 3s: {cache_get('k1')}")

        # cached_fetch
        async def fetcher():
            print("  fetch_fn called")
            return "fetched_value"

        r = await cached_fetch("k2", 60, fetcher)
        print(f"first call: {r}")
        r = await cached_fetch("k2", 60, fetcher)  # 应该命中缓存
        print(f"second call (cached): {r}")

        # 单飞
        results = await asyncio.gather(*[
            single_flight("k3", 60, fetcher) for _ in range(5)
        ])
        print(f"single flight results: {results}")

        print(f"\nstats: {cache_stats()}")

    asyncio.run(test())
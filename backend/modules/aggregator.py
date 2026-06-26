"""
高并发 RSS 聚合器 - 复刻 worldmonitor list-feed-digest.ts
- 20 路并发抓取
- 单源 8s 超时 / 总 25s 截止
- 每源最多 5 条
- 每分类最多 20 条
- 内存缓存（10分钟，替代 Redis）
- 威胁分级 + 主题分类
"""
import asyncio
import re
import time
from datetime import datetime
import httpx
import feedparser

try:
    from data.sources import ALL_SOURCES, BY_CATEGORY, get_sources_by_category, get_source_stats
    from data.classifier import classify_threat, get_threat_distribution, THREAT_LEVELS
except ImportError:
    from backend.data.sources import ALL_SOURCES, BY_CATEGORY, get_sources_by_category, get_source_stats
    from backend.data.classifier import classify_threat, get_threat_distribution, THREAT_LEVELS


# 聚合参数（参考 worldmonitor）
ITEMS_PER_FEED = 5            # 每个源最多 5 条
MAX_ITEMS_PER_CATEGORY = 20   # 每个分类最多 20 条
FEED_TIMEOUT_S = 8.0          # 单源超时
OVERALL_DEADLINE_S = 25.0      # 总超时
BATCH_CONCURRENCY = 20        # 并发抓取数
CACHE_TTL_S = 600             # 缓存 10 分钟

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NEXUS-Radar/3.0 (+https://github.com/local)"


# ============================================================
# 内存缓存
# ============================================================
class TTLCache:
    """简易 TTL 缓存，替代 Redis"""
    def __init__(self):
        self._store = {}

    def get(self, key: str):
        item = self._store.get(key)
        if not item:
            return None
        if time.time() - item["ts"] > item["ttl"]:
            del self._store[key]
            return None
        return item["value"]

    def set(self, key: str, value, ttl: int = CACHE_TTL_S):
        self._store[key] = {"value": value, "ts": time.time(), "ttl": ttl}

    def stats(self):
        return {
            "keys": len(self._store),
            "valid": sum(1 for v in self._store.values() if time.time() - v["ts"] <= v["ttl"]),
        }


cache = TTLCache()


# ============================================================
# 单源抓取
# ============================================================
async def fetch_one_feed(client: httpx.AsyncClient, source: dict) -> list[dict]:
    """抓取单个 RSS 源"""
    items = []
    try:
        r = await client.get(
            source["url"], timeout=FEED_TIMEOUT_S, follow_redirects=True,
            headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, application/xml, */*"}
        )
        if r.status_code != 200:
            return items
        feed = feedparser.parse(r.content)
        for entry in feed.entries[:ITEMS_PER_FEED]:
            title = entry.get("title", "").strip()
            if not title:
                continue
            summary = entry.get("summary", "") or entry.get("description", "")
            summary = re.sub(r"<[^>]+>", "", summary).strip()[:300]
            text = f"{title} {summary}"
            # 威胁分级
            threat = classify_threat(text)
            items.append({
                "title": title[:200],
                "summary": summary,
                "url": entry.get("link", ""),
                "source": source["name"],
                "source_url": source["url"],
                "lang": source["lang"],
                "region": source["region"],
                "category": source["category"],
                "published": entry.get("published", ""),
                # 威胁分级
                "severity": threat["level"],
                "score": threat["score"],
                "topic": threat["topic"],
                "matched_keywords": threat["matched_keywords"],
                "label": threat["label"],
                "label_cn": threat["label_cn"],
                "color": threat["color"],
            })
    except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError):
        pass  # 网络问题，静默跳过
    except Exception:
        pass
    return items


# ============================================================
# 批量并发抓取
# ============================================================
async def fetch_batch(sources: list[dict]) -> list[dict]:
    """并发抓取一批源，受 BATCH_CONCURRENCY 限制"""
    sem = asyncio.Semaphore(BATCH_CONCURRENCY)
    async with httpx.AsyncClient() as client:
        async def _fetch(src):
            async with sem:
                return await fetch_one_feed(client, src)
        results = await asyncio.gather(*[_fetch(s) for s in sources], return_exceptions=True)
    items = []
    for r in results:
        if isinstance(r, list):
            items.extend(r)
    return items


# ============================================================
# 按分类聚合
# ============================================================
async def aggregate_category(category: str) -> list[dict]:
    """聚合指定分类的所有源"""
    cache_key = f"cat:{category}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    sources = get_sources_by_category(category)
    items = await fetch_batch(sources)
    # 按威胁分排序，截断 MAX_ITEMS_PER_CATEGORY
    items.sort(key=lambda x: x["score"], reverse=True)
    items = items[:MAX_ITEMS_PER_CATEGORY]
    cache.set(cache_key, items)
    return items


# ============================================================
# 按变体聚合（推荐主入口）
# ============================================================
async def aggregate_variant(variant: str = "full", max_per_cat: int = 5) -> dict:
    """按变体聚合所有分类"""
    cache_key = f"variant:{variant}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # 取该变体所有源
    try:
        from data.sources import get_sources_by_variant
    except ImportError:
        from backend.data.sources import get_sources_by_variant
    sources = get_sources_by_variant(variant)

    # 按 category 分组，并发抓取
    by_cat = {}
    for s in sources:
        by_cat.setdefault(s["category"], []).append(s)

    # 限制每个分类最多抓取 max_per_cat 条
    cat_results = {}
    async def _cat(cat_name, cat_sources):
        items = await fetch_batch(cat_sources)
        items.sort(key=lambda x: x["score"], reverse=True)
        cat_results[cat_name] = items[:MAX_ITEMS_PER_CATEGORY]

    await asyncio.gather(*[_cat(n, s) for n, s in by_cat.items()])

    # 汇总
    all_items = []
    for items in cat_results.values():
        all_items.extend(items)
    all_items.sort(key=lambda x: x["score"], reverse=True)

    result = {
        "variant": variant,
        "items_by_category": cat_results,
        "all_items": all_items[:100],
        "total_items": len(all_items),
        "total_sources": len(sources),
        "categories_scanned": list(cat_results.keys()),
        "threat_distribution": get_threat_distribution(all_items),
        "scanned_at": datetime.now().isoformat(),
    }
    cache.set(cache_key, result, ttl=CACHE_TTL_S)
    return result


# ============================================================
# 全量聚合（不受 variant 限制）
# ============================================================
async def aggregate_all(limit_per_cat: int = 5) -> dict:
    """全量聚合，按分类返回"""
    cache_key = "aggregate_all"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # 按 category 分组，每个分类并发抓取
    cat_results = {}
    async def _cat(cat_name):
        sources = get_sources_by_category(cat_name)
        items = await fetch_batch(sources)
        items.sort(key=lambda x: x["score"], reverse=True)
        cat_results[cat_name] = items[:MAX_ITEMS_PER_CATEGORY]

    await asyncio.gather(*[_cat(c) for c in BY_CATEGORY.keys()])

    all_items = []
    for items in cat_results.values():
        all_items.extend(items)
    all_items.sort(key=lambda x: x["score"], reverse=True)

    result = {
        "module": "aggregator",
        "items_by_category": cat_results,
        "all_items": all_items[:200],
        "total_items": len(all_items),
        "total_sources": len(ALL_SOURCES),
        "categories_scanned": list(cat_results.keys()),
        "threat_distribution": get_threat_distribution(all_items),
        "cache_stats": cache.stats(),
        "scanned_at": datetime.now().isoformat(),
    }
    cache.set(cache_key, result, ttl=CACHE_TTL_S)
    return result


# ============================================================
# 单独获取某个分类的摘要
# ============================================================
async def get_feed_digest(category: str = None, limit: int = 30) -> dict:
    """获取 feed digest（参考 list-feed-digest）"""
    if category:
        items = await aggregate_category(category)
        return {
            "category": category,
            "items": items[:limit],
            "total": len(items),
            "scanned_at": datetime.now().isoformat(),
        }
    # 没指定分类 -> 返回全量 top
    full = await aggregate_all()
    return {
        "category": "all",
        "items": full["all_items"][:limit],
        "total": full["total_items"],
        "threat_distribution": full["threat_distribution"],
        "scanned_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    async def test():
        import json
        print(">>> 测试单分类聚合 (intel)...")
        items = await aggregate_category("intel")
        print(f"抓到 {len(items)} 条 intel 类目")
        for it in items[:3]:
            print(f"  [{it['severity']:8s}] {it['title'][:80]}")
        print()
        print(">>> 测试全量聚合...")
        result = await aggregate_all()
        print(f"总条数: {result['total_items']}")
        print(f"威胁分布: {result['threat_distribution']}")
        print(f"缓存: {result['cache_stats']}")

    asyncio.run(test())

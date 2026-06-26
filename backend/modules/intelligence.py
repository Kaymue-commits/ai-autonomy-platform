"""
全球情报模块 - 类似 worldmonitor / situation-monitor
聚合多源全球新闻、地缘事件、CII国家关键基础设施指数
"""
import asyncio
import re
from datetime import datetime
import feedparser
import httpx

# 全球情报源（地缘/科技/政治）
INTEL_SOURCES = {
    "BBC-World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Reuters-World": "https://www.reutersagency.com/feed/?best-topics=top-news&post_type=best",
    "Al-Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "RT-News": "https://www.rt.com/rss/",
    "DW-News": "https://rss.dw.com/rdf/rss-en-all",
    "LeMonde": "https://www.lemonde.fr/rss/une.xml",
    "Global-Times": "https://www.globaltimes.cn/rss/outbound.xml",
    "Nikkei": "https://asia.nikkei.com/rss/feed/nar",
    "Defense-Blog": "https://defence-blog.com/feed",
    "Janes": "https://www.janes.com/feeds/news",
}

# CII 关键基础设施类别（参考 worldmonitor 54国CII指数）
CII_CATEGORIES = [
    "能源", "金融", "通信", "交通", "水利", "政府", "医疗", "国防", "农业", "制造"
]

# 地缘关键词
GEOPOLITICAL_KEYWORDS = {
    "sanction": 25, "embargo": 30, "treaty": 15, "alliance": 12,
    "military": 18, "missile": 25, "nuclear": 30, "cyberattack": 22,
    "election": 12, "coup": 30, "summit": 10, "summit": 10,
    "diplomatic": 8, "tariff": 20, "trade_war": 25, "OPEC": 18,
    "NATO": 20, "BRICS": 15, "G7": 12, "G20": 10,
    "invasion": 30, "ceasefire": 20, "proxy_war": 25,
}

def score_intel(text: str) -> int:
    text_lower = text.lower()
    score = 0
    for kw, pts in GEOPOLITICAL_KEYWORDS.items():
        if kw.lower() in text_lower:
            score += pts
    return min(score, 100)


def classify_severity(score: int) -> str:
    if score >= 70:
        return "critical"   # 严重
    if score >= 40:
        return "elevated"   # 升级
    if score >= 20:
        return "moderate"   # 中度
    return "low"             # 低


# CII国家指数（54国模拟数据，基于公开情报的相对权重）
CII_INDEX = {
    "美国": 92, "中国": 89, "俄罗斯": 78, "德国": 81, "法国": 76,
    "英国": 79, "日本": 83, "印度": 71, "巴西": 58, "加拿大": 74,
    "澳大利亚": 69, "韩国": 80, "以色列": 75, "伊朗": 62, "沙特": 65,
    "土耳其": 60, "乌克兰": 55, "波兰": 58, "芬兰": 72, "瑞典": 73,
    "挪威": 70, "荷兰": 75, "比利时": 67, "西班牙": 64, "意大利": 66,
    "墨西哥": 52, "阿根廷": 48, "南非": 50, "尼日利亚": 41, "埃及": 53,
    "阿联酋": 68, "卡塔尔": 64, "科威特": 56, "伊拉克": 38, "巴基斯坦": 47,
    "印尼": 54, "马来西亚": 57, "新加坡": 81, "泰国": 55, "越南": 49,
    "菲律宾": 46, "新西兰": 67, "智利": 51, "哥伦比亚": 45, "秘鲁": 42,
    "葡萄牙": 60, "希腊": 49, "捷克": 63, "匈牙利": 56, "罗马尼亚": 52,
    "保加利亚": 47, "塞尔维亚": 44, "白俄罗斯": 53, "哈萨克斯坦": 51, "乌兹别克斯坦": 43,
}


async def fetch_intel_feed(client: httpx.AsyncClient, name: str, url: str) -> list[dict]:
    items = []
    try:
        r = await client.get(url, timeout=12.0, follow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 GeoRadar/2.0"})
        if r.status_code != 200:
            return items
        feed = feedparser.parse(r.content)
        for entry in feed.entries[:15]:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or ""
            text = f"{title} {summary}"
            score = score_intel(text)
            if score < 10:
                continue
            items.append({
                "title": title[:200],
                "summary": re.sub(r"<[^>]+>", "", summary)[:300],
                "url": entry.get("link", ""),
                "source": name,
                "severity": classify_severity(score),
                "score": score,
                "category": "geopolitical",
                "timestamp": datetime.now().isoformat(),
            })
    except Exception:
        pass
    return items


async def scan_global_intel() -> dict:
    """扫描全球情报源"""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_intel_feed(client, n, u) for n, u in INTEL_SOURCES.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    all_events = []
    for r in results:
        if isinstance(r, list):
            all_events.extend(r)
    all_events.sort(key=lambda x: x["score"], reverse=True)
    return {
        "module": "global_intel",
        "events": all_events[:30],
        "cii_index": CII_INDEX,
        "cii_categories": CII_CATEGORIES,
        "total_sources": len(INTEL_SOURCES),
        "scanned_at": datetime.now().isoformat(),
    }


# 模拟航班追踪（OSINT War Room 风格）
FLIGHT_TRACKS = [
    {"callsign": "AFR123", "from": "巴黎", "to": "纽约", "lat": 48.85, "lon": 2.35, "alt": 35000, "type": "commercial"},
    {"callsign": "UAL456", "from": "旧金山", "to": "东京", "lat": 36.0, "lon": -150.0, "alt": 38000, "type": "commercial"},
    {"callsign": "AEF789", "from": "兰德施泰因", "to": "中东", "lat": 35.0, "lon": 40.0, "alt": 41000, "type": "military"},
    {"callsign": "RAF999", "from": "阿克罗蒂里", "to": "未知", "lat": 32.0, "lon": 33.0, "alt": 28000, "type": "military"},
    {"callsign": "SIN001", "from": "新加坡", "to": "迪拜", "lat": 12.0, "lon": 70.0, "alt": 36000, "type": "commercial"},
]


def get_flight_snapshot():
    """获取模拟航班快照"""
    import random
    for f in FLIGHT_TRACKS:
        f["lat"] += random.uniform(-0.5, 0.5)
        f["lon"] += random.uniform(-0.5, 0.5)
        f["alt"] += random.randint(-100, 100)
    return FLIGHT_TRACKS

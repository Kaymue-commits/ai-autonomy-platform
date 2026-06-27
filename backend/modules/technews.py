"""
科技情报模块 - 全球实时科技热点新闻
聚合主流科技媒体 RSS + Hacker News API
"""
import asyncio
import re
from datetime import datetime
import feedparser
import httpx


# 科技新闻源 (精选高质量, 全球覆盖)
TECH_NEWS_SOURCES = {
    # 国际主流
    "TechCrunch":    "https://techcrunch.com/feed/",
    "TheVerge":      "https://www.theverge.com/rss/index.xml",
    "Engadget":      "https://www.engadget.com/rss.xml",
    "ArsTechnica":   "https://feeds.arstechnica.com/arstechnica/index",
    "Wired":         "https://www.wired.com/feed/rss",
    "MIT-TechReview":"https://www.technologyreview.com/feed/",
    "Recode":        "https://www.recode.net/rss/index.xml",
    "Gizmodo":       "https://gizmodo.com/rss",
    "CNET":          "https://www.cnet.com/rss/news/",
    "ExtremeTech":   "https://www.extremetech.com/feed",
    # 中文科技
    "36氪":          "https://36kr.com/feed",
    "虎嗅":          "https://www.huxiu.com/rss/0.xml",
    "少数派":        "https://sspai.com/feed",
    "InfoQ中文":     "https://www.infoq.cn/feed.xml",
    "极客公园":      "https://www.geekpark.net/rss",
    # Hacker News (Top)
    "HackerNews-Top":"https://hnrss.org/frontpage",
    "HackerNews-Best":"https://hnrss.org/best",
}


# 科技热点关键词 (用于评分)
TECH_HOT_KEYWORDS = {
    "ChatGPT": 90, "GPT-5": 95, "Claude": 85, "Gemini": 82, "Llama": 78,
    "AGI": 88, "Sora": 90, "AI agent": 80, "multimodal": 75,
    "quantum": 80, "quantum computing": 92, "qubit": 78,
    "nuclear fusion": 90, "fusion": 75, "ITER": 80,
    "neuralink": 88, "brain-computer": 85, "BCI": 82,
    "Tesla": 70, "SpaceX": 78, "Starship": 85, "Starlink": 72,
    "Apple": 65, "Vision Pro": 85, "iPhone": 55, "Microsoft": 60,
    "Google": 60, "Meta": 58, "Nvidia": 75, "GPU": 65, "H100": 80, "Blackwell": 88,
    "robot": 70, "humanoid": 82, "Figure": 78, "Boston Dynamics": 80,
    "self-driving": 72, "FSD": 70, "autonomous": 65,
    "breakthrough": 70, "world first": 75, "first ever": 75,
    "battery": 60, "solid state": 75, "perovskite": 70,
    "gene editing": 80, "CRISPR": 82, "mRNA": 70,
    "cyberattack": 75, "data breach": 70, "zero-day": 78,
    "blockchain": 50, "crypto": 45, "bitcoin": 40, "ethereum": 40,
    "metaverse": 45, "AR/VR": 60, "wearable": 50,
    "semiconductor": 70, "TSMC": 72, "ASML": 75, "3nm": 78, "2nm": 85,
    "EV": 55, "electric vehicle": 55, "BYD": 60,
    "rocket": 70, "reusable": 65, "mars": 75,
}


# 区域/分类标签
def classify_tech(text: str) -> str:
    tl = text.lower()
    if any(k in tl for k in ["ai", "gpt", "llm", "chatbot", "machine learning", "neural"]):
        return "AI"
    if any(k in tl for k in ["quantum", "qubit", "supercomputer"]):
        return "量子计算"
    if any(k in tl for k in ["fusion", "nuclear", "battery", "solar", "energy"]):
        return "能源"
    if any(k in tl for k in ["spacex", "starship", "nasa", "mars", "rocket", "satellite"]):
        return "航天"
    if any(k in tl for k in ["neuralink", "brain", "crispr", "gene", "mRNA"]):
        return "生物科技"
    if any(k in tl for k in ["robot", "humanoid", "autonomous", "self-driving"]):
        return "机器人"
    if any(k in tl for k in ["apple", "google", "microsoft", "meta", "tesla"]):
        return "大公司"
    if any(k in tl for k in ["cyberattack", "breach", "vulnerability", "hack"]):
        return "网络安全"
    if any(k in tl for k in ["chip", "semiconductor", "gpu", "tsmc", "asml", "nm"]):
        return "半导体"
    return "综合"


def score_tech_news(text: str) -> int:
    text_lower = text.lower()
    score = 30
    for kw, pts in TECH_HOT_KEYWORDS.items():
        if kw.lower() in text_lower:
            score = max(score, pts)
    return min(score, 100)


async def fetch_tech_feed(client: httpx.AsyncClient, name: str, url: str) -> list[dict]:
    items = []
    try:
        r = await client.get(url, timeout=12.0, follow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0 NEXUS-TechRadar/2.0"})
        if r.status_code != 200:
            return items
        feed = feedparser.parse(r.content)
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            text = f"{title} {summary}"
            score = score_tech_news(text)
            if score < 35:
                continue
            items.append({
                "title": title[:200],
                "summary": re.sub(r"<[^>]+>", "", summary)[:280],
                "url": entry.get("link", ""),
                "source": name,
                "score": score,
                "category": classify_tech(text),
                "timestamp": datetime.now().isoformat(),
            })
    except Exception:
        pass
    return items


async def scan_tech_news() -> dict:
    """扫描全球科技新闻"""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_tech_feed(client, n, u) for n, u in TECH_NEWS_SOURCES.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    all_news = []
    for r in results:
        if isinstance(r, list):
            all_news.extend(r)
    all_news.sort(key=lambda x: x["score"], reverse=True)
    # 分类分布
    cat_dist = {}
    for n in all_news:
        cat_dist[n["category"]] = cat_dist.get(n["category"], 0) + 1
    return {
        "module": "tech_news",
        "news": all_news[:50],
        "category_distribution": cat_dist,
        "total_sources": len(TECH_NEWS_SOURCES),
        "total_news": len(all_news),
        "scanned_at": datetime.now().isoformat(),
    }

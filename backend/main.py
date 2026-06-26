"""
AI Autonomy Platform - Backend Core
全球AI需求雷达 + 自动对接 + 自动开发 + 跨境收款
"""
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

# 让 backend/modules 能被 import
sys.path.insert(0, str(Path(__file__).parent))

import feedparser
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# 新模块
from modules.intelligence import scan_global_intel, get_flight_snapshot
from modules.finance import scan_finance
from modules.osint import get_conflict_snapshot, generate_event_stream
from modules.freelance import scan_freelance
from modules.energy import get_energy_snapshot
from modules.ainews import scan_ai_news

# ===== 配置 =====
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.json"

def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "creem_api_key": os.getenv("CREEM_API_KEY", ""),
        "creem_webhook_secret": os.getenv("CREEM_WEBHOOK_SECRET", ""),
        "alipay_app_id": os.getenv("ALIPAY_APP_ID", ""),
        "alipay_private_key": os.getenv("ALIPAY_PRIVATE_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "contact_email": os.getenv("CONTACT_EMAIL", ""),
        "discord_webhook": os.getenv("DISCORD_WEBHOOK", ""),
        "wecom_webhook": os.getenv("WECOM_WEBHOOK", ""),
    }

CONFIG = load_config()

# ===== 数据模型 =====
class Demand(BaseModel):
    id: str
    title: str
    description: str
    source: str
    url: str
    region: str
    city: str
    lat: float
    lon: float
    category: str
    score: int  # 0-100
    estimated_value_usd: float
    contact_info: str = ""
    status: str = "scanned"  # scanned / matched / contacted / quoted / won / lost
    created_at: str
    updated_at: str

# ===== 城市/地区映射 =====
CITY_DB = {
    "旧金山": ("北美", -122.4194, 37.7749),
    "纽约": ("北美", -74.0060, 40.7128),
    "洛杉矶": ("北美", -118.2437, 34.0522),
    "多伦多": ("北美", -79.3832, 43.6532),
    "西雅图": ("北美", -122.3321, 47.6062),
    "芝加哥": ("北美", -87.6298, 41.8781),
    "伦敦": ("欧洲", -0.1276, 51.5074),
    "巴黎": ("欧洲", 2.3522, 48.8566),
    "柏林": ("欧洲", 13.4050, 52.5200),
    "阿姆斯特丹": ("欧洲", 4.9041, 52.3676),
    "苏黎世": ("欧洲", 8.5417, 47.3769),
    "斯德哥尔摩": ("欧洲", 18.0686, 59.3293),
    "东京": ("亚洲", 139.6503, 35.6762),
    "首尔": ("亚洲", 126.9780, 37.5665),
    "新加坡": ("亚洲", 103.8198, 1.3521),
    "香港": ("亚洲", 114.1694, 22.3193),
    "上海": ("亚洲", 121.4737, 31.2304),
    "孟买": ("亚洲", 72.8777, 19.0760),
    "迪拜": ("中东", 55.2708, 25.2048),
    "特拉维夫": ("中东", 34.7818, 32.0853),
    "利雅得": ("中东", 46.6753, 24.7136),
    "圣保罗": ("南美", -46.6333, -23.5505),
    "墨西哥城": ("南美", -99.1332, 19.4326),
    "悉尼": ("大洋洲", 151.2093, -33.8688),
}

# ===== 高价值AI需求关键词 =====
HIGH_VALUE_KEYWORDS = {
    "AI Agent": 25, "AI automation": 22, "workflow automation": 20,
    "RAG": 18, "LLM integration": 20, "GPT-4": 15, "Claude": 15, "Gemini": 12,
    "computer vision": 18, "speech-to-text": 15, "TTS": 12, "voice clone": 18,
    "image generation": 15, "video generation": 22, "Sora": 25, "Suno": 18,
    "Stable Diffusion": 15, "Midjourney": 12, "ComfyUI": 20,
    "fine-tuning": 18, "embedding": 10, "vector database": 12,
    "chatbot": 10, "customer support AI": 15, "sales AI": 18,
    "marketing AI": 15, "SEO AI": 12, "content generation": 15,
    "data analysis": 12, "predictive analytics": 15, "MLOps": 18,
    "robotic process automation": 18, "RPA": 12, "AI consulting": 20,
    "bounty": 30, "hiring AI engineer": 25, "contract": 15,
    "MVP": 18, "prototype": 12, "production deployment": 15,
}

# ===== 全球信息源 (RSS/公开API) =====
SOURCES = {
    "ProductHunt": "https://www.producthunt.com/feed",
    "HackerNews": "https://hnrss.org/frontpage",
    "Reddit-ML": "https://www.reddit.com/r/MachineLearning/.rss",
    "Reddit-AI": "https://www.reddit.com/r/artificial/.rss",
    "GitHub-Trending": "https://mshibanami.github.io/github-trending/feed.atom",
    "IndieHackers": "https://www.indiehackers.com/feed.xml",
    "Crunchbase": "https://news.crunchbase.com/feed/",
    "TechCrunch": "https://techcrunch.com/feed/",
    "VentureBeat": "https://venturebeat.com/feed/",
    "36氪": "https://36kr.com/feed",
    "虎嗅": "https://www.huxiu.com/rss/0.xml",
}

# ===== 应用初始化 =====
app = FastAPI(title="AI Autonomy Radar", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存数据存储
DEMANDS: dict[str, Demand] = {}
DEMANDS_HISTORY: list[dict] = []

# SSE订阅者
SUBSCRIBERS: list[asyncio.Queue] = []

async def broadcast(event_type: str, data: dict):
    for q in SUBSCRIBERS:
        try:
            await q.put({"event": event_type, "data": json.dumps(data, ensure_ascii=False)})
        except Exception:
            pass

async def log_broadcast(msg: str, msg_type: str = "info"):
    await broadcast("log", {"msg": msg, "type": msg_type, "time": datetime.now().isoformat()})

# ===== 工具函数 =====
def detect_city(text: str) -> tuple[str, tuple] | None:
    """从文本中检测城市"""
    for city, info in CITY_DB.items():
        if city in text:
            return city, info
    # 英文城市
    en_map = {"San Francisco": "旧金山", "New York": "纽约", "London": "伦敦",
              "Berlin": "柏林", "Tokyo": "东京", "Singapore": "新加坡",
              "Dubai": "迪拜", "Toronto": "多伦多", "Sydney": "悉尼"}
    for en, zh in en_map.items():
        if en.lower() in text.lower():
            return zh, CITY_DB[zh]
    return None

def score_demand(text: str) -> tuple[int, float]:
    """AI需求评分 (0-100) + 预估价值USD"""
    text_lower = text.lower()
    score = 0
    for kw, pts in HIGH_VALUE_KEYWORDS.items():
        if kw.lower() in text_lower:
            score += pts
    score = min(score, 100)

    # 价值估算
    if score >= 80:
        value = 5000 + (score - 80) * 200
    elif score >= 60:
        value = 1000 + (score - 60) * 200
    elif score >= 40:
        value = 200 + (score - 40) * 40
    else:
        value = max(50, score * 5)

    return score, value

def classify_category(text: str) -> str:
    """分类"""
    text_lower = text.lower()
    if any(k in text_lower for k in ["video", "sora", "runway", "pika", "video generation"]):
        return "视频生成"
    if any(k in text_lower for k in ["image", "midjourney", "stable diffusion", "comfyui", "diffusion"]):
        return "图像生成"
    if any(k in text_lower for k in ["voice", "tts", "speech", "audio", "music", "suno"]):
        return "语音音乐"
    if any(k in text_lower for k in ["agent", "automation", "workflow", "rpa"]):
        return "Agent自动化"
    if any(k in text_lower for k in ["chatbot", "rag", "llm", "gpt", "claude"]):
        return "大模型应用"
    if any(k in text_lower for k in ["vision", "ocr", "detection", "recognition"]):
        return "计算机视觉"
    if any(k in text_lower for k in ["data", "analytics", "predict"]):
        return "数据分析"
    return "其他AI"

# ===== 抓取引擎 =====
async def fetch_source(client: httpx.AsyncClient, name: str, url: str) -> list[dict]:
    """抓取单个信息源"""
    items = []
    try:
        r = await client.get(url, timeout=15.0, follow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0 AI-Radar/1.0"})
        if r.status_code != 200:
            await log_broadcast(f"⚠ {name} HTTP {r.status_code}", "warn")
            return items
        feed = feedparser.parse(r.content)
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            link = entry.get("link", "")
            text = f"{title} {summary}"
            score, value = score_demand(text)
            if score < 25:  # 过滤低价值
                continue
            city_info = detect_city(text)
            city, region, lon, lat = "网络", "全球", 0.0, 0.0
            if city_info:
                city, (region, lon, lat) = city_info
            category = classify_category(text)
            items.append({
                "title": title[:200],
                "description": re.sub(r"<[^>]+>", "", summary)[:500],
                "url": link,
                "source": name,
                "region": region,
                "city": city,
                "lat": lat, "lon": lon,
                "category": category,
                "score": score,
                "estimated_value_usd": value,
            })
    except Exception as e:
        await log_broadcast(f"❌ {name}: {type(e).__name__}", "error")
    return items

async def fetch_hn_jobs() -> list[dict]:
    """HackerNews Who's Hiring - 高价值需求金矿"""
    items = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            # 最新"Who's Hiring"帖
            r = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            ids = r.json()[:50]
            for sid in ids:
                sr = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                d = sr.json()
                if not d: continue
                title = d.get("title", "")
                if "hiring" not in title.lower() and "ask hn" not in title.lower() and "freelance" not in title.lower():
                    continue
                # 抓取评论
                kids = d.get("kids", [])[:30]
                comments_text = ""
                for kid in kids[:20]:
                    kr = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{kid}.json")
                    c = kr.json()
                    if c and c.get("text"):
                        comments_text += " " + re.sub(r"<[^>]+>", " ", c["text"])
                full = f"{title} {comments_text}"
                score, value = score_demand(full)
                if score < 30: continue
                city_info = detect_city(full)
                city, region, lon, lat = "网络", "全球", 0.0, 0.0
                if city_info:
                    city, (region, lon, lat) = city_info
                items.append({
                    "title": title[:200],
                    "description": f"HN招聘帖ID: {sid} | {len(kids)}条评论",
                    "url": f"https://news.ycombinator.com/item?id={sid}",
                    "source": "HackerNews-Jobs",
                    "region": region,
                    "city": city,
                    "lat": lat, "lon": lon,
                    "category": classify_category(full),
                    "score": min(score + 5, 100),  # HN质量加成
                    "estimated_value_usd": value * 1.5,
                })
    except Exception as e:
        await log_broadcast(f"❌ HN抓取失败: {e}", "error")
    return items

async def scan_all_sources():
    """扫描所有信息源"""
    await log_broadcast("🔍 开始扫描全球AI需求源...", "info")
    async with httpx.AsyncClient() as client:
        tasks = [fetch_source(client, name, url) for name, url in SOURCES.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_items = []
        for r in results:
            if isinstance(r, list):
                all_items.extend(r)
        # HN Who is hiring
        hn_items = await fetch_hn_jobs()
        all_items.extend(hn_items)

    await log_broadcast(f"✅ 扫描完成: {len(all_items)} 条候选", "success")

    # 去重 + 入库
    seen_titles = set()
    new_count = 0
    for item in all_items:
        key = item["title"][:50]
        if key in seen_titles: continue
        seen_titles.add(key)

        did = f"{item['source']}-{hash(key) & 0xFFFFFF:06x}"
        if did in DEMANDS: continue

        demand = Demand(
            id=did,
            title=item["title"],
            description=item["description"],
            url=item["url"],
            source=item["source"],
            region=item["region"],
            city=item["city"],
            lat=item["lat"],
            lon=item["lon"],
            category=item["category"],
            score=item["score"],
            estimated_value_usd=item["estimated_value_usd"],
            status="matched",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        DEMANDS[did] = demand
        DEMANDS_HISTORY.append(demand.dict())
        new_count += 1

        await broadcast("scan", {
            **demand.dict(),
            "match": True,
            "contact": False,
            "revenue": 0,
        })
        if new_count <= 5:
            await log_broadcast(f"📍 {item['city']}/{item['region']} | {item['title'][:60]} | 价值${item['estimated_value_usd']:.0f}", "success")

    await log_broadcast(f"🆕 新增 {new_count} 条高质量需求 (评分≥25)", "success")
    return new_count

# ===== API路由 =====
@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = ROOT / "frontend" / "globe.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))

@app.get("/api/demands")
async def list_demands(region: str = None, min_score: int = 0, limit: int = 100):
    items = list(DEMANDS.values())
    if region and region != "all":
        items = [d for d in items if d.region == region]
    items = [d for d in items if d.score >= min_score]
    items.sort(key=lambda x: x.score, reverse=True)
    return JSONResponse([d.dict() for d in items[:limit]])

@app.get("/api/stats")
async def stats():
    total_value = sum(d.estimated_value_usd for d in DEMANDS.values() if d.status in ["won", "quoted"])
    return {
        "total_demands": len(DEMANDS),
        "total_value_usd": total_value,
        "by_region": {},
        "by_status": {},
    }

@app.get("/api/stream")
async def stream(request: Request):
    """SSE 实时推送"""
    queue = asyncio.Queue()
    SUBSCRIBERS.append(queue)

    async def gen() -> AsyncGenerator:
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=10)
                    yield item
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            SUBSCRIBERS.remove(queue)
    return EventSourceResponse(gen())

@app.post("/api/scan")
async def trigger_scan():
    """手动触发扫描"""
    asyncio.create_task(scan_all_sources())
    return {"status": "scanning"}

@app.post("/api/contact/{demand_id}")
async def contact_demand(demand_id: str):
    """自动对接指定需求"""
    demand = DEMANDS.get(demand_id)
    if not demand:
        return JSONResponse({"error": "demand not found"}, status_code=404)

    try:
        # 调用对接模块
        from modules.contact import auto_contact
        result = await auto_contact(demand, CONFIG)
        demand.status = "contacted"
        demand.updated_at = datetime.now().isoformat()
        await log_broadcast(f"📨 已对接 [{demand.city}] {demand.title[:40]}", "success")
        await broadcast("scan", {**demand.dict(), "contact": True})
        return result
    except Exception as e:
        await log_broadcast(f"对接失败 [{demand_id}]: {e}", "error")
        return JSONResponse({"error": str(e), "demand_id": demand_id}, status_code=500)

@app.post("/api/build/{demand_id}")
async def build_solution(demand_id: str):
    """自动开发方案"""
    demand = DEMANDS.get(demand_id)
    if not demand:
        return JSONResponse({"error": "demand not found"}, status_code=404)

    try:
        from modules.builder import auto_build
        result = await auto_build(demand, CONFIG)
        demand.status = "quoted"
        demand.updated_at = datetime.now().isoformat()
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ===== Creem 收款 Webhook =====
@app.post("/api/webhook/creem")
async def creem_webhook(request: Request):
    """Creem 支付回调"""
    payload = await request.json()
    await log_broadcast(f"💰 Creem收款: {payload}", "success")
    # 业务逻辑：入账、通知用户
    return {"received": True}

# ============================================================
# 新增模块 API 路由（情报 / 金融 / OSINT / 自由职业 / 能源 / AI新闻）
# ============================================================

@app.get("/api/intel")
async def api_global_intel():
    """全球情报仪表盘（worldmonitor 风格）"""
    try:
        data = await scan_global_intel()
        await log_broadcast(f"🌍 全球情报: 抓取 {len(data['events'])} 条事件", "info")
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/flights")
async def api_flights():
    """航班追踪（OSINT War Room 风格）"""
    return {"flights": get_flight_snapshot()}

@app.get("/api/finance")
async def api_finance():
    """金融雷达（OpenStock / QuantDinger / Profitmaker 风格）"""
    try:
        data = await scan_finance()
        await log_broadcast(f"💰 金融数据: {len(data['crypto'])}币 + {len(data['stock_indices'])}指数 + {len(data['prediction_markets'])}预测市场", "info")
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/osint")
async def api_osint():
    """OSINT冲突追踪（war-map / crisismap 风格）"""
    try:
        data = get_conflict_snapshot()
        await log_broadcast(f"🛰 OSINT: {len(data['hotspots'])}热点 + {len(data['cyber_events'])}网络战 + {len(data['military_movements'])}调动", "info")
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/osint/events")
async def api_osint_events():
    """OSINT 事件流（ACLED 风格）"""
    return {"events": generate_event_stream(25)}

@app.get("/api/freelance")
async def api_freelance():
    """自由职业机会（Devalopers / Propoplex / HN Who's Hiring 风格）"""
    try:
        data = await scan_freelance()
        await log_broadcast(f"💼 自由职业: {len(data['jobs'])}条 | 总价值 ${data['total_value_usd']:,}", "info")
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/energy")
async def api_energy():
    """能源监控（ioBroker.energiefluss / solarsynkv3 风格）"""
    try:
        data = get_energy_snapshot()
        await log_broadcast(f"⚡ 能源: 全球负载 {data['global_load_gw']}GW / {data['global_capacity_gw']}GW", "info")
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/ainews")
async def api_ainews():
    """AI新闻雷达（Horizon / AiLert / Auto-News 风格）"""
    try:
        data = await scan_ai_news()
        await log_broadcast(f"📰 AI新闻: {len(data['news'])}条 / {data['total_sources']}源", "info")
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# 模块统一聚合状态
@app.get("/api/modules/status")
async def modules_status():
    """所有模块状态"""
    from data.sources import get_source_stats
    stats = get_source_stats()
    return {
        "sources": stats,
        "modules": {
            "aggregator": "ready",
            "classifier": "ready",
            "cache": "ready",
            "specialized": "ready (GDELT/USGS/ACLED/FIRMS)",
            "contact": "ready",
            "builder": "ready",
            "payment": "ready",
        },
        "version": "1.1.0",
    }


# ===== v1.1.0: Aggregator + Specialized 路由 =====
@app.get("/api/feed")
async def get_feed(
    category: str = None,
    variant: str = None,
    limit: int = 100,
    min_threat: str = "info",
):
    """
    获取聚合的新闻流 (来自 149 个数据源)
    category: 指定分类 (intel/politics/ai/finance/crypto/security...)
    variant: 'full' / 'tech' / 'finance'
    min_threat: info / low / medium / high / critical
    """
    from modules.aggregator import get_feed_digest, aggregate_variant, THREAT_LEVELS
    # 威胁等级过滤
    min_score = THREAT_LEVELS.get(min_threat, {"score": 0})["score"]
    if category:
        result = await get_feed_digest(category=category, limit=limit)
        items = [it for it in result["items"] if it.get("score", 0) >= min_score]
        return {**result, "items": items, "total": len(items)}
    if variant and variant != "all":
        result = await aggregate_variant(variant=variant)
        items = [it for it in result["all_items"] if it.get("score", 0) >= min_score][:limit]
        return {
            "variant": variant,
            "items": items,
            "total": len(items),
            "threat_distribution": result["threat_distribution"],
            "scanned_at": result["scanned_at"],
        }
    # 默认全量 top
    result = await get_feed_digest(category=None, limit=limit)
    items = [it for it in result["items"] if it.get("score", 0) >= min_score]
    return {**result, "items": items, "total": len(items)}


@app.get("/api/feed/variants")
async def list_variants():
    """列出所有可用的 variants 和分类"""
    from data.sources import get_source_stats, BY_VARIANT, BY_CATEGORY
    stats = get_source_stats()
    return {
        "total_sources": stats["total_sources"],
        "variants": {
            v: {
                "count": len(srcs),
                "categories": sorted(set(s["category"] for s in srcs)),
            } for v, srcs in BY_VARIANT.items() if srcs
        },
        "categories": {c: len(srcs) for c, srcs in BY_CATEGORY.items()},
        "regions": stats["by_region"],
    }


@app.get("/api/events/geolocated")
async def get_geolocated_events():
    """
    获取带经纬度的真实事件 (USGS 地震 / NASA FIRMS 火灾)
    可直接显示在 3D 地球上
    """
    from modules.specialized import fetch_earthquakes, fetch_wildfires
    quakes, fires = await asyncio.gather(fetch_earthquakes(), fetch_wildfires())
    geo = []
    for q in quakes:
        geo.append({**q, "source_type": "usgs", "category": "earthquake"})
    for f in fires:
        geo.append({**f, "source_type": "nasa", "category": "wildfire"})
    return {
        "events": geo,
        "count": len(geo),
        "source_breakdown": {
            "USGS (earthquakes)": len(quakes),
            "NASA FIRMS (fires)": len(fires),
        },
        "scanned_at": datetime.now().isoformat(),
    }


@app.get("/api/events/gdelt")
async def get_gdelt_events(theme: str = "CONFLICT", timespan: str = "3d", max: int = 50):
    """GDELT 全球事件数据库"""
    from modules.specialized import fetch_gdelt_events
    events = await fetch_gdelt_events(theme=theme, limit=max)
    return {
        "events": events,
        "count": len(events),
        "theme": theme,
        "timespan": timespan,
        "scanned_at": datetime.now().isoformat(),
    }


# ===== 新增: 数据源管理 / 专业数据 / 威胁分级元数据 =====
@app.get("/api/sources")
async def list_sources(category: str = None, region: str = None):
    """列出所有数据源 (149 个分类 RSS 源)"""
    from data.sources import ALL_SOURCES, get_source_stats, BY_CATEGORY, BY_REGION
    if category:
        return {
            "category": category,
            "sources": BY_CATEGORY.get(category, []),
            "count": len(BY_CATEGORY.get(category, [])),
        }
    if region:
        return {
            "region": region,
            "sources": BY_REGION.get(region, []),
            "count": len(BY_REGION.get(region, [])),
        }
    return {
        "sources": ALL_SOURCES,
        "stats": get_source_stats(),
    }


@app.get("/api/sources/stats")
async def sources_stats():
    """数据源统计"""
    from data.sources import get_source_stats
    return get_source_stats()


@app.get("/api/specialized")
async def specialized_data():
    """专业数据统一入口 (USGS 地震 / NASA FIRMS / OpenSky 航班 / GDELT 事件)"""
    from modules.specialized import scan_all_specialized
    try:
        data = await scan_all_specialized()
        await log_broadcast(
            f"🛰 专业源: 地震 {data['total_quakes']} | 火灾 {data['total_fires']} | 航班 {data['total_flights']} | GDELT {data['total_gdelt']}",
            "info"
        )
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/specialized/earthquakes")
async def api_earthquakes():
    """USGS 24h 地震数据"""
    from modules.specialized import fetch_earthquakes
    return {"earthquakes": await fetch_earthquakes()}


@app.get("/api/specialized/flights")
async def api_flights_real(limit: int = 50):
    """OpenSky 实时航班"""
    from modules.specialized import fetch_flights_opensky
    return {"flights": await fetch_flights_opensky(limit=limit)}


@app.get("/api/threat-levels")
async def threat_levels():
    """威胁分级元数据"""
    from data.classifier import THREAT_LEVELS, TOPIC_KEYWORDS
    return {
        "levels": THREAT_LEVELS,
        "topics": list(TOPIC_KEYWORDS.keys()),
    }


@app.get("/api/aggregator")
async def aggregator_all():
    """全量聚合 (149 源并发抓取，按分类返回)"""
    from modules.aggregator import aggregate_all
    try:
        data = await aggregate_all()
        await log_broadcast(
            f"📡 聚合: {data['total_items']} 条 / {data['total_sources']} 源 / 分布 {data['threat_distribution']}",
            "info"
        )
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ===== 后台扫描任务 =====
@app.on_event("startup")
async def startup():
    async def loop_demand():
        """需求雷达扫描"""
        await asyncio.sleep(3)
        await log_broadcast("🚀 AI Autonomy Radar 已启动", "success")
        while True:
            try:
                await scan_all_sources()
            except Exception as e:
                await log_broadcast(f"扫描异常: {e}", "error")
            await asyncio.sleep(600)  # 每10分钟

    async def loop_fast_modules():
        """快刷新模块：金融/能源/OSINT/航班（高频数据，2-5秒刷一次）"""
        await asyncio.sleep(2)
        while True:
            try:
                # 金融
                fin = await scan_finance()
                await broadcast("module_finance", fin)
                # 能源
                en = get_energy_snapshot()
                await broadcast("module_energy", en)
                # OSINT 冲突快照
                os = get_conflict_snapshot()
                await broadcast("module_osint", os)
                # 航班
                await broadcast("module_flights", {"flights": get_flight_snapshot()})
            except Exception as e:
                await log_broadcast(f"快模块异常: {e}", "error")
            await asyncio.sleep(5)

    async def loop_slow_modules():
        """慢刷新模块：情报/AI新闻/自由职业（RSS抓取，5分钟一次）"""
        await asyncio.sleep(8)
        while True:
            try:
                intel = await scan_global_intel()
                await broadcast("module_intel", intel)
                news = await scan_ai_news()
                await broadcast("module_ainews", news)
                fl = await scan_freelance()
                await broadcast("module_freelance", fl)
                # OSINT 事件流
                await broadcast("module_events", {"events": generate_event_stream(15)})
            except Exception as e:
                await log_broadcast(f"慢模块异常: {e}", "error")
            await asyncio.sleep(300)

    async def loop_specialized():
        """专业数据源：USGS地震/NASA FIRMS/OpenSky航班/GDELT（3分钟一次）"""
        await asyncio.sleep(15)
        while True:
            try:
                from modules.specialized import scan_all_specialized
                data = await scan_all_specialized()
                await broadcast("module_specialized", data)
                await log_broadcast(
                    f"🛰 专业源: 地震 {data['total_quakes']} | 火灾 {data['total_fires']} | 航班 {data['total_flights']} | GDELT {data['total_gdelt']}",
                    "info"
                )
            except Exception as e:
                await log_broadcast(f"专业源异常: {e}", "error")
            await asyncio.sleep(180)

    async def loop_aggregator():
        """全量 RSS 聚合器：149 源并发抓取（10分钟一次，配合缓存）"""
        await asyncio.sleep(30)
        while True:
            try:
                from modules.aggregator import aggregate_all
                data = await aggregate_all()
                await broadcast("module_aggregator", data)
                await log_broadcast(
                    f"📡 聚合 {data['total_items']} 条 / {data['total_sources']} 源 / 分布 {data['threat_distribution']}",
                    "info"
                )
            except Exception as e:
                await log_broadcast(f"聚合器异常: {e}", "error")
            await asyncio.sleep(600)

    asyncio.create_task(loop_demand())
    asyncio.create_task(loop_fast_modules())
    asyncio.create_task(loop_slow_modules())
    asyncio.create_task(loop_specialized())
    asyncio.create_task(loop_aggregator())

# ===== 静态文件 =====
app.mount("/static", StaticFiles(directory=str(ROOT / "frontend")), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=7777, reload=True)
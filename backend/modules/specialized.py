"""
专业数据 API 集成 - 接入 worldmonitor 提到的专业数据库
- USGS 地震数据 (公开 JSON API)
- NASA FIRMS 野火数据 (公开 API)
- OpenSky 航班追踪 (公开 API)
- GDELT 事件数据库 (公开 API)
- Polymarket 预测市场 (公开 API)
- OpenMeteo 天气 (公开 API)
"""
import asyncio
from datetime import datetime, timedelta
import httpx


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NEXUS-Radar/3.0"


# ============================================================
# USGS 地震数据
# ============================================================
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"


def _classify_quake(mag: float) -> str:
    if mag >= 7.0:
        return "critical"
    if mag >= 6.0:
        return "high"
    if mag >= 5.0:
        return "medium"
    if mag >= 3.0:
        return "low"
    return "info"


async def fetch_earthquakes() -> list[dict]:
    """USGS 全球 24h 内地震数据"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(USGS_URL, headers={"User-Agent": UA})
            if r.status_code != 200:
                return []
            data = r.json()
            quakes = []
            for feat in data.get("features", [])[:50]:
                props = feat.get("properties", {})
                geo = feat.get("geometry", {})
                coords = geo.get("coordinates", [0, 0, 0])
                mag = props.get("mag", 0) or 0
                if mag < 2.5:
                    continue
                severity = _classify_quake(mag)
                quakes.append({
                    "id": feat.get("id", ""),
                    "type": "earthquake",
                    "place": props.get("place", "未知"),
                    "magnitude": round(mag, 1),
                    "depth_km": round(coords[2] or 0, 1),
                    "lat": coords[1],
                    "lon": coords[0],
                    "time": datetime.fromtimestamp(props.get("time", 0) / 1000).isoformat() if props.get("time") else "",
                    "url": props.get("url", ""),
                    "severity": severity,
                    "score": min(100, int(mag * 12)),
                    "title": f"M{mag:.1f} - {props.get('place', '未知')}",
                    "summary": f"震级 M{mag:.1f} 深度 {coords[2]:.0f}km",
                    "source": "USGS",
                })
            quakes.sort(key=lambda x: x["magnitude"], reverse=True)
            return quakes
    except Exception:
        return []


# ============================================================
# NASA FIRMS 野火数据
# ============================================================
# NASA FIRMS 公开 WMS/API (无 key 部分有限，这里用 MODIS 24h 摘要)
FIRMS_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/v1/anonymous/MODIS_NRT/world/1/24"


async def fetch_wildfires() -> list[dict]:
    """NASA FIRMS 24h 野火检测"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(FIRMS_URL, headers={"User-Agent": UA})
            if r.status_code != 200:
                return []
            lines = r.text.strip().split("\n")
            if len(lines) < 2:
                return []
            header = lines[0].split(",")
            idx = {h: i for i, h in enumerate(header)}
            fires = []
            for line in lines[1:51]:  # 最多50个
                parts = line.split(",")
                if len(parts) < len(header):
                    continue
                try:
                    lat = float(parts[idx.get("latitude", 1)])
                    lon = float(parts[idx.get("longitude", 2)])
                    brightness = float(parts[idx.get("brightness", 3)])
                    confidence = int(parts[idx.get("confidence", 8)] or 50)
                    frp = float(parts[idx.get("frp", 12)] or 0)  # 火灾辐射功率
                except (ValueError, IndexError):
                    continue
                # 威胁分级
                if frp > 200 or confidence >= 90:
                    severity = "high"
                    score = 80
                elif frp > 100:
                    severity = "medium"
                    score = 55
                else:
                    severity = "low"
                    score = 35
                fires.append({
                    "type": "wildfire",
                    "lat": lat,
                    "lon": lon,
                    "brightness_k": round(brightness, 1),
                    "confidence": confidence,
                    "frp_mw": round(frp, 1),
                    "acquired": parts[idx.get("acq_date", 5)] + " " + parts[idx.get("acq_time", 6)],
                    "satellite": parts[idx.get("satellite", 7)],
                    "severity": severity,
                    "score": score,
                    "title": f"野火热点 @ {lat:.2f},{lon:.2f} (FRP {frp:.0f}MW)",
                    "summary": f"卫星 {parts[idx.get('satellite', 7)]} 亮度 {brightness:.1f}K 置信 {confidence}%",
                    "source": "NASA FIRMS",
                })
            fires.sort(key=lambda x: x["frp_mw"], reverse=True)
            return fires
    except Exception:
        return []


# ============================================================
# OpenSky 航班追踪
# ============================================================
OPENSKY_URL = "https://opensky-network.org/api/states/all"


async def fetch_flights_opensky(limit: int = 50) -> list[dict]:
    """OpenSky Network 全球航班实时状态"""
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(OPENSKY_URL, headers={"User-Agent": UA}, params={"lamin": -60, "lomax": 180, "lamin2": -60, "lomax2": 180})
            if r.status_code != 200:
                return []
            data = r.json()
            states = data.get("states", []) or []
            flights = []
            for s in states[:limit]:
                # OpenSky state vector
                # [icao24, callsign, origin_country, time_position, last_contact,
                #  longitude, latitude, baro_altitude, on_ground, velocity,
                #  true_track, vertical_rate, sensors, geo_altitude, squawk, spi, position_source]
                icao = s[0] or ""
                callsign = (s[1] or "").strip()
                country = s[2] or ""
                lon = s[5]
                lat = s[6]
                alt = s[7] or s[13] or 0
                on_ground = s[8]
                velocity = s[9] or 0
                heading = s[10] or 0
                if lat is None or lon is None:
                    continue
                # 推测军航（基于呼号前缀）
                military_prefix = ["AEF", "RAF", "RCH", "RRR", "CNV", "VIVI", "VVIP", "AFGSC"]
                is_military = any(callsign.startswith(p) for p in military_prefix)
                flights.append({
                    "icao24": icao,
                    "callsign": callsign or icao,
                    "origin_country": country,
                    "lat": round(lat, 3),
                    "lon": round(lon, 3),
                    "altitude_m": round(alt, 0) if alt else 0,
                    "on_ground": bool(on_ground),
                    "velocity_ms": round(velocity, 1) if velocity else 0,
                    "heading": round(heading, 1) if heading else 0,
                    "type": "military" if is_military else "commercial",
                    "severity": "medium" if is_military else "info",
                    "score": 70 if is_military else 30,
                    "source": "OpenSky",
                })
            return flights
    except Exception:
        return []


# ============================================================
# GDELT 事件数据库 (GKG - Global Knowledge Graph)
# ============================================================
# GDELT DOC 2.0 API - 实时全球事件新闻
GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


async def fetch_gdelt_events(theme: str = "CONFLICT", limit: int = 30) -> list[dict]:
    """GDELT 事件流 (按主题过滤)"""
    query = f"(theme:{theme} OR theme:MILITARY OR theme:CRISISLEX) sourcelang:english"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                GDELT_DOC_URL,
                params={
                    "query": query,
                    "mode": "ArtList",
                    "maxrecords": limit,
                    "format": "json",
                    "sort": "DateDesc",
                    "timespan": "3d",  # 最近 3 天
                },
                headers={"User-Agent": UA}
            )
            if r.status_code != 200:
                return []
            data = r.json()
            articles = data.get("articles", [])
            events = []
            for a in articles[:limit]:
                title = a.get("title", "")
                url = a.get("url", "")
                domain = a.get("domain", "")
                lang = a.get("language", "en")
                # 威胁分级
                try:
                    from data.classifier import classify_threat
                except ImportError:
                    from backend.data.classifier import classify_threat
                threat = classify_threat(title)
                events.append({
                    "title": title[:200],
                    "url": url,
                    "source": domain,
                    "lang": lang,
                    "seendate": a.get("seendate", ""),
                    "socialimage": a.get("socialimage", ""),
                    "severity": threat["level"],
                    "score": threat["score"],
                    "topic": threat["topic"],
                    "matched_keywords": threat["matched_keywords"],
                    "label": threat["label"],
                    "label_cn": threat["label_cn"],
                    "color": threat["color"],
                    "source_db": "GDELT",
                })
            events.sort(key=lambda x: x["score"], reverse=True)
            return events
    except Exception:
        return []


# ============================================================
# Open-Meteo 天气（地震带/火山区天气）
# ============================================================
OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_weather(lat: float, lon: float) -> dict:
    """获取指定位置的天气"""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                OPENMETEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,wind_speed_10m,weather_code",
                    "timezone": "auto"
                }
            )
            if r.status_code != 200:
                return {}
            data = r.json()
            cur = data.get("current", {})
            return {
                "temperature_c": cur.get("temperature_2m"),
                "wind_kmh": cur.get("wind_speed_10m"),
                "weather_code": cur.get("weather_code"),
                "lat": lat,
                "lon": lon,
            }
    except Exception:
        return {}


# ============================================================
# 统一入口
# ============================================================
async def scan_all_specialized() -> dict:
    """并发抓取所有专业源"""
    earthquakes, wildfires, flights, gdelt = await asyncio.gather(
        fetch_earthquakes(),
        fetch_wildfires(),
        fetch_flights_opensky(limit=50),
        fetch_gdelt_events(theme="CONFLICT", limit=30),
        return_exceptions=True
    )
    # 安全处理异常
    earthquakes = earthquakes if isinstance(earthquakes, list) else []
    wildfires = wildfires if isinstance(wildfires, list) else []
    flights = flights if isinstance(flights, list) else []
    gdelt = gdelt if isinstance(gdelt, list) else []

    # 全部合并成统一事件流（带坐标，用于地球叠加）
    geo_events = []
    for q in earthquakes:
        geo_events.append({**q, "category": "earthquake"})
    for f in wildfires:
        geo_events.append({**f, "category": "wildfire"})

    return {
        "module": "specialized",
        "earthquakes": earthquakes,
        "wildfires": wildfires,
        "flights": flights,
        "gdelt_events": gdelt,
        "geo_events": geo_events,  # 带坐标的可视化事件
        "total_quakes": len(earthquakes),
        "total_fires": len(wildfires),
        "total_flights": len(flights),
        "total_gdelt": len(gdelt),
        "scanned_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    async def test():
        import json
        print(">>> USGS 地震...")
        q = await fetch_earthquakes()
        print(f"  抓到 {len(q)} 条")
        for it in q[:3]:
            print(f"  M{it['magnitude']} {it['place']} @{it['lat']:.2f},{it['lon']:.2f}")
        print()
        print(">>> OpenSky 航班...")
        f = await fetch_flights_opensky(limit=10)
        print(f"  抓到 {len(f)} 条")
        for it in f[:3]:
            print(f"  {it['callsign']} ({it['origin_country']}) @{it['lat']:.2f},{it['lon']:.2f} alt={it['altitude_m']}m")
        print()
        print(">>> GDELT 冲突事件...")
        g = await fetch_gdelt_events(theme="CONFLICT", limit=10)
        print(f"  抓到 {len(g)} 条")
        for it in g[:3]:
            print(f"  [{it['severity']:8s}] {it['title'][:80]}")

    asyncio.run(test())

"""
太空追踪模块 - 全球卫星实时位置 + 轨道可视化
数据源:
  - CelesTrack TLE API (官方公开 NORAD 数据)
  - Starlink / Active / Military / Stations / Weather 分类
  - Starlink 信息补充: orbitalradar.com/starlink-tracker

实现简化版 SGP4 位置计算 (纯 Python, 无外部依赖)
"""
import math
import time
from datetime import datetime, timezone
import httpx


# ============================================================
# CelesTrack TLE 数据源
# ============================================================
# GROUP 参数 (https://celestrak.com/NORAD/elements/gp.php?GROUP=xxx&FORMAT=json)
TLE_GROUPS = {
    "starlink":  "starlink",     # Starlink 星座
    "active":    "active",        # 所有活跃卫星
    "stations":  "stations",     # 空间站 (ISS, CSS 天宫等)
    "weather":   "weather",      # 气象卫星
    "geo":       "geo",           # 地球同步卫星
    "navigation": "gnss",         # 导航卫星 (GPS/北斗/伽利略/GLONASS)
    # 军事卫星: 用 OBJECT_TYPE=military 或 CATEGORY=46
}

# 军事相关分类 (CelesTrack CATEGORY)
MILITARY_CATEGORIES = [46]  # 46 = Military

# 缓存 (TLE 数据 + 抓取时间)
_cache = {}  # group -> {"sats": [...], "fetched_at": ts}
_CACHE_TTL = 6 * 3600  # 6 小时 (TLE 数据更新频率低)

# 地球常数
EARTH_RADIUS_KM = 6371.0
MU_EARTH = 398600.4418  # km^3/s^2


# ============================================================
# TLE 解析
# ============================================================
def parse_gp(obj: dict) -> dict | None:
    """解析 CelesTrack GP JSON 格式 (含 MEAN_MOTION/INCLINATION 等字段)"""
    try:
        name = obj.get("OBJECT_NAME") or obj.get("NAME") or ""
        norad_id = str(obj.get("NORAD_CAT_ID") or "")
        i = math.radians(float(obj["INCLINATION"]))
        raan = math.radians(float(obj["RA_OF_ASC_NODE"]))
        e = float(obj["ECCENTRICITY"])
        argp = math.radians(float(obj["ARG_OF_PERICENTER"]))
        M = math.radians(float(obj["MEAN_ANOMALY"]))
        n = float(obj["MEAN_MOTION"])  # rev/day
        # 历元 ISO 时间
        epoch_str = obj.get("EPOCH") or ""
        from datetime import datetime, timezone
        epoch_dt = datetime.fromisoformat(epoch_str.replace("Z", "+00:00"))
        epoch_ts = epoch_dt.timestamp()
        # 半长轴
        n_rad_s = n * 2 * math.pi / 86400.0
        a = (MU_EARTH / (n_rad_s ** 2)) ** (1.0 / 3.0)
        alt = a - EARTH_RADIUS_KM
        period_min = 1440.0 / n if n > 0 else 0
        return {
            "norad_id": norad_id,
            "inclination_deg": math.degrees(i),
            "raan_deg": math.degrees(raan),
            "eccentricity": e,
            "argp_deg": math.degrees(argp),
            "mean_anomaly_deg": math.degrees(M),
            "mean_motion": n,
            "semi_major_km": a,
            "altitude_km": alt,
            "period_min": period_min,
            "epoch_ts": epoch_ts,
            "_i": i, "_raan": raan, "_e": e, "_argp": argp, "_M": M, "_n": n, "_a": a, "_epoch_ts": epoch_ts,
        }
    except Exception:
        return None


def parse_tle(line1: str, line2: str) -> dict:
    """解析两行 TLE, 提取轨道根数"""
    try:
        # Line 1: 1 NNNNNC YYYYNNN.NNNNNNNN +.NNNNNNNN +NNNNN-N +NNNNN-N N N NNNNN
        # Line 2: 2 NNNNN III.IIII RRR.RRRR EEEEEEE PPP.PPPP MMM.MMMM NN.NNNNNNNNNNNNNN
        i = math.radians(float(line2[8:16].strip()))           # 倾角
        raan = math.radians(float(line2[17:25].strip()))         # 升交点经度
        e = float("0." + line2[26:33].strip())                  # 偏心率
        argp = math.radians(float(line2[34:42].strip()))        # 近地点幅角
        M = math.radians(float(line2[43:51].strip()))           # 平近点角
        n = float(line2[52:63].strip())                         # 平均运动 (rev/day)
        # 历元 (Line1 第 19-32 字符)
        epoch_str = line1[18:32].strip()
        year = int(epoch_str[:2])
        year = 2000 + year if year < 57 else 1900 + year
        day_of_year = float(epoch_str[2:])
        # 历元时间戳
        from datetime import timedelta
        epoch_dt = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day_of_year - 1)
        epoch_ts = epoch_dt.timestamp()
        # 半长轴 (km): n (rev/day) -> a = (MU / (2πn/86400)^2)^(1/3)
        n_rad_s = n * 2 * math.pi / 86400.0  # rad/s
        a = (MU_EARTH / (n_rad_s ** 2)) ** (1.0 / 3.0)
        # 高度
        alt = a - EARTH_RADIUS_KM
        # 周期 (分钟)
        period_min = 1440.0 / n if n > 0 else 0
        # NORAD ID
        norad_id = line1[2:7].strip()
        return {
            "norad_id": norad_id,
            "inclination_deg": math.degrees(i),
            "raan_deg": math.degrees(raan),
            "eccentricity": e,
            "argp_deg": math.degrees(argp),
            "mean_anomaly_deg": math.degrees(M),
            "mean_motion": n,
            "semi_major_km": a,
            "altitude_km": alt,
            "period_min": period_min,
            "epoch_ts": epoch_ts,
            "_i": i, "_raan": raan, "_e": e, "_argp": argp, "_M": M, "_n": n, "_a": a, "_epoch_ts": epoch_ts,
        }
    except Exception:
        return None


# ============================================================
# 简化位置计算 (基于开普勒轨道, 忽略 J2 摄动)
# ============================================================
def calc_sat_position(orbit: dict, at_ts: float = None) -> tuple:
    """计算卫星在 at_ts 时刻的地心经纬度+高度
    返回 (lat_deg, lon_deg, alt_km)
    """
    if at_ts is None:
        at_ts = time.time()
    i = orbit["_i"]
    raan = orbit["_raan"]
    e = orbit["_e"]
    argp = orbit["_argp"]
    a = orbit["_a"]
    n_rad_s = orbit["_n"] * 2 * math.pi / 86400.0
    epoch_ts = orbit["_epoch_ts"]
    M0 = orbit["_M"]

    # 时间差 (秒)
    dt = at_ts - epoch_ts
    # 当前平近点角
    M = M0 + n_rad_s * dt
    M = M % (2 * math.pi)

    # 解开普勒方程求偏近点角 E: M = E - e*sin(E) (牛顿迭代)
    E = M
    for _ in range(6):
        E = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))

    # 真近点角 ν
    nu = 2 * math.atan2(
        math.sqrt(1 + e) * math.sin(E / 2),
        math.sqrt(1 - e) * math.cos(E / 2)
    )

    # 升交点幅角 u = ω + ν
    u = argp + nu

    # 轨道平面坐标 (忽略 r 摄动, 用 a)
    r = a * (1 - e * math.cos(E))
    x_orb = r * math.cos(u)
    y_orb = r * math.sin(u)

    # 转惯性系 (旋转 -Ω 绕 Z, -i 绕 X)
    cos_O, sin_O = math.cos(raan), math.sin(raan)
    cos_i, sin_i = math.cos(i), math.sin(i)
    X = cos_O * x_orb - sin_O * y_orb * cos_i
    Y = sin_O * x_orb + cos_O * y_orb * cos_i
    Z = y_orb * sin_i

    # 纬度
    lat = math.atan2(Z, math.sqrt(X * X + Y * Y))
    # 惯性经度
    lon_inertial = math.atan2(Y, X)
    # 减格林尼治恒星时 → 地固经度
    gmst = _gmst(at_ts)
    lon = lon_inertial - gmst
    # 归一化到 [-π, π]
    lon = ((lon + math.pi) % (2 * math.pi)) - math.pi

    return math.degrees(lat), math.degrees(lon), r - EARTH_RADIUS_KM


def _gmst(ts: float) -> float:
    """格林尼治平恒星时 (rad), 简化公式"""
    from datetime import datetime, timezone
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    # 儒略日
    year = dt.year
    month = dt.month
    day = dt.day
    if month <= 2:
        year -= 1
        month += 12
    A = year // 100
    B = 2 - A + A // 4
    JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
    JD += dt.hour / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
    T = (JD - 2451545.0) / 36525.0
    # GMST (deg)
    gmst_deg = 280.46061837 + 360.98564736629 * (JD - 2451545.0) + 0.000387933 * T * T - T * T * T / 38710000.0
    return math.radians(gmst_deg % 360.0)


# ============================================================
# TLE 数据抓取
# ============================================================
async def fetch_tle_group(client: httpx.AsyncClient, group: str, max_count: int = 200) -> list[dict]:
    """抓取指定分类的卫星 TLE (CelesTrack API)
    group 是内部组名 (会作为返回的 group 字段); URL 用 TLE_GROUPS 映射"""
    api_group = TLE_GROUPS.get(group, group)
    # 先尝试 JSON 格式 (含 MEAN_ELEMENT 信息更全)
    urls = [
        f"https://celestrak.org/NORAD/elements/gp.php?GROUP={api_group}&FORMAT=json",
        f"https://celestrak.org/NORAD/elements/gp.php?CATNR=&GROUP={api_group}&FORMAT=tle",  # 备用 TLE 文本格式
    ]
    sats = []
    try:
        r = await client.get(urls[0], timeout=30.0, headers={"User-Agent": "Mozilla/5.0 NEXUS-Radar"})
        if r.status_code == 200:
            data = r.json()
            for obj in data[:max_count]:
                # 优先 GP 格式 (CelesTrack 新 API)
                orbit = None
                if "MEAN_MOTION" in obj:
                    orbit = parse_gp(obj)
                else:
                    l1 = obj.get("TLE_LINE1") or ""
                    l2 = obj.get("TLE_LINE2") or ""
                    if l1 and l2:
                        orbit = parse_tle(l1, l2)
                if not orbit:
                    continue
                name = obj.get("OBJECT_NAME") or obj.get("NAME") or ""
                sats.append({
                    "name": name,
                    "norad_id": orbit["norad_id"],
                    "group": group,
                    "orbit": orbit,
                })
    except Exception:
        pass
    return sats


async def fetch_military_sats(client: httpx.AsyncClient, max_count: int = 200) -> list[dict]:
    """抓取军事相关卫星: 从 active 列表过滤 USA-/Cosmos/Yaogan/KMS 等军事前缀"""
    sats = []
    try:
        r = await client.get(
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json",
            timeout=30.0, headers={"User-Agent": "Mozilla/5.0 NEXUS-Radar"}
        )
        if r.status_code == 200:
            data = r.json()
            mil_prefixes = ("USA-", "Cosmos", "Yaogan", "KMS", "Navid", "OFEQ",
                             "Lacrosse", "Orion", "Mentor", "Trumpet", "Vortex",
                             "SDS", "Mercury", "SBIRS", "WGS", "AEHF", "MUOS",
                             "GPS", "BeiDou", "GLONASS", "Galileo", "QZS")
            for obj in data:
                name = obj.get("OBJECT_NAME") or ""
                if not any(name.startswith(p) or name.startswith(p.upper()) for p in mil_prefixes):
                    continue
                orbit = parse_gp(obj) if "MEAN_MOTION" in obj else None
                if not orbit:
                    l1 = obj.get("TLE_LINE1") or ""
                    l2 = obj.get("TLE_LINE2") or ""
                    if l1 and l2:
                        orbit = parse_tle(l1, l2)
                if not orbit:
                    continue
                sats.append({
                    "name": name,
                    "norad_id": orbit["norad_id"],
                    "group": "military",
                    "orbit": orbit,
                })
                if len(sats) >= max_count:
                    break
    except Exception:
        pass
    return sats


# ============================================================
# Starlink 补充信息 (orbitalradar.com)
# ============================================================
# Starlink 星座基本信息 (公开统计)
STARLINK_INFO = {
    "total_launched": 7213,
    "total_active": 6420,
    "total_deorbited": 793,
    "v1_count": 4408,
    "v2_mini_count": 2012,
    "orbital_planes": 72,
    "altitude_km": 550,
    "inclination_deg": 53.0,
    "info_source": "orbitalradar.com/starlink-tracker",
    "info_url": "https://orbitalradar.com/starlink-tracker",
}


# ============================================================
# 主入口: 获取所有卫星快照
# ============================================================
async def get_satellite_snapshot() -> dict:
    """获取所有卫星实时位置快照"""
    now_ts = time.time()
    # 检查缓存
    need_fetch = []
    for grp in ["starlink", "stations", "weather", "navigation", "geo"]:
        cached = _cache.get(grp)
        if not cached or (now_ts - cached["fetched_at"]) > _CACHE_TTL:
            need_fetch.append(grp)

    if need_fetch:
        async with httpx.AsyncClient(verify=False, timeout=60.0, follow_redirects=True) as client:
            # 并发抓取 (传内部组名; fetch_tle_group 内部会映射到 CelesTrack API 名)
            tasks = []
            for grp in need_fetch:
                max_c = 200 if grp == "starlink" else (50 if grp == "stations" else 150)
                tasks.append(fetch_tle_group(client, grp, max_count=max_c))
            tasks.append(fetch_military_sats(client, max_count=150))
            results = await _gather_tasks(tasks)
            # 更新缓存
            fetch_groups = need_fetch + ["military"]
            for grp, result in zip(fetch_groups, results):
                if result:
                    _cache[grp] = {"sats": result, "fetched_at": now_ts}

    # 汇总所有卫星
    all_sats = []
    group_counts = {}
    # 为前端可视化挑选代表性的卫星 (避免一次渲染 6000 颗卡顿)
    render_sats = []
    # 代表性轨道线 (每组最多 3 条, 在保留 orbit 时生成)
    orbit_traces = []
    seen_groups_for_trace = {}

    for grp, cached in _cache.items():
        sats = cached["sats"]
        group_counts[grp] = len(sats)
        # 计算每个卫星当前位置
        positions = []
        trace_count = 0
        for idx, s in enumerate(sats):
            try:
                lat, lon, alt = calc_sat_position(s["orbit"], now_ts)
                pos_item = {
                    "name": s["name"],
                    "norad_id": s["norad_id"],
                    "group": s["group"],
                    "lat": round(lat, 4),
                    "lon": round(lon, 4),
                    "alt_km": round(alt, 1),
                    "inclination": round(s["orbit"]["inclination_deg"], 1),
                    "period_min": round(s["orbit"]["period_min"], 1),
                    "raan": round(s["orbit"]["raan_deg"], 1),
                }
                positions.append(pos_item)
                # 生成代表性轨道线 (每组最多 3 条)
                if trace_count < 3 and grp in ("starlink", "military", "stations", "navigation", "weather", "geo"):
                    trace = _build_orbit_trace(s["orbit"], now_ts)
                    if trace:
                        orbit_traces.append({
                            "group": grp,
                            "name": s["name"],
                            "inclination": pos_item["inclination"],
                            "altitude": round(alt, 1),
                            "points": trace,
                        })
                    trace_count += 1
            except Exception:
                continue
        all_sats.extend(positions)
        # 渲染采样: starlink 取前 50, 其他全取
        if grp == "starlink":
            render_sats.extend(positions[:50])
        else:
            render_sats.extend(positions)

    return {
        "module": "satellite",
        "total_tracked": len(all_sats),
        "group_counts": group_counts,
        "starlink_info": STARLINK_INFO,
        "render_sats": render_sats[:300],  # 前端渲染上限 300 颗
        "all_sats": all_sats[:800],       # 右侧面板展示上限 800 颗
        "orbit_traces": orbit_traces,      # 代表性轨道线 (供前端画椭圆)
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_orbit_trace(orbit: dict, now_ts: float, points: int = 90) -> list[dict]:
    """生成一条完整轨道的经纬度采样点 (使用与 calc_sat_position 一致的算法)"""
    pts = []
    a = orbit["_a"]
    period_sec = 2 * math.pi * math.sqrt(a ** 3 / MU_EARTH)
    for k in range(points + 1):
        t = now_ts - period_sec * (k / points)  # 回溯一个周期
        try:
            lat, lon, alt = calc_sat_position(orbit, t)
            pts.append({"lat": round(lat, 4), "lon": round(lon, 4), "alt": round(alt, 1)})
        except Exception:
            continue
    return pts


async def _gather_tasks(tasks):
    """并发等待所有任务, 异常返回 []"""
    import asyncio
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out = []
    for r in results:
        if isinstance(r, Exception):
            out.append([])
        else:
            out.append(r)
    return out

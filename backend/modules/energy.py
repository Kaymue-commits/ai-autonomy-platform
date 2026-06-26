"""
能源监控模块 - 类似 ioBroker.energiefluss / solarsynkv3 / tplink-energy-monitor
全球能源结构、电网负载、光伏/储能流可视化
"""
import random
from datetime import datetime


# 全球主要电网区域
GRID_REGIONS = [
    {"id": "us-ercot", "name": "美国德州ERCOT", "lat": 30.0, "lon": -97.0, "capacity_gw": 90, "load_pct": 78},
    {"id": "us-caiso", "name": "美国加州CAISO", "lat": 37.0, "lon": -120.0, "capacity_gw": 65, "load_pct": 72},
    {"id": "eu-entsoe", "name": "欧洲ENTSO-E", "lat": 50.0, "lon": 10.0, "capacity_gw": 1020, "load_pct": 65},
    {"id": "cn-state-grid", "name": "中国国家电网", "lat": 35.0, "lon": 110.0, "capacity_gw": 2950, "load_pct": 68},
    {"id": "jp-occto", "name": "日本OCCTO", "lat": 36.0, "lon": 138.0, "capacity_gw": 280, "load_pct": 62},
    {"id": "in-posoco", "name": "印度POSOCO", "lat": 22.0, "lon": 78.0, "capacity_gw": 417, "load_pct": 81},
    {"id": "br-ons", "name": "巴西ONS", "lat": -15.0, "lon": -55.0, "capacity_gw": 175, "load_pct": 70},
    {"id": "au-aemo", "name": "澳大利亚AEMO", "lat": -30.0, "lon": 145.0, "capacity_gw": 65, "load_pct": 75},
]


# 全球能源结构占比 (%)
ENERGY_MIX = [
    {"source": "煤电", "pct": 36, "color": "#616161", "co2_g_per_kwh": 820},
    {"source": "天然气", "pct": 23, "color": "#ffa726", "co2_g_per_kwh": 490},
    {"source": "水电", "pct": 16, "color": "#42a5f5", "co2_g_per_kwh": 24},
    {"source": "核电", "pct": 10, "color": "#ab47bc", "co2_g_per_kwh": 12},
    {"source": "风电", "pct": 7, "color": "#26c6da", "co2_g_per_kwh": 11},
    {"source": "光伏", "pct": 6, "color": "#ffca28", "co2_g_per_kwh": 41},
    {"source": "其他可再生", "pct": 2, "color": "#66bb6a", "co2_g_per_kwh": 38},
]


# 单个家庭/工业微电网模拟（参考 energiefluss-erweitert 风格）
MICROGRID = {
    "solar_kw": 12.5,        # 光伏当前出力
    "solar_peak_kw": 15.0,
    "battery_soc_pct": 68,   # 电池荷电状态
    "battery_kw": 3.2,       # 充(+)/放(-) 功率
    "grid_kw": -1.8,         # 正=从电网取,负=反向送电网
    "home_load_kw": 4.5,
    "ev_charging_kw": 0,
    "ev_connected": False,
}


def _tick_microgrid():
    """模拟微电网状态变化"""
    # 光伏随时间波动
    hour = datetime.now().hour
    if 6 <= hour <= 18:
        factor = max(0, 1 - abs(hour - 12) / 6) + random.uniform(-0.1, 0.1)
        MICROGRID["solar_kw"] = round(max(0, MICROGRID["solar_peak_kw"] * factor), 2)
    else:
        MICROGRID["solar_kw"] = 0.0
    # 电池策略：白天充电,晚上放电
    solar = MICROGRID["solar_kw"]
    home = MICROGRID["home_load_kw"] + random.uniform(-0.5, 0.5)
    MICROGRID["home_load_kw"] = round(home, 2)
    net = solar - home  # 净功率
    if net > 0:
        # 多余 -> 充电池
        charge = min(net, 5.0)
        if MICROGRID["battery_soc_pct"] < 95:
            MICROGRID["battery_kw"] = round(charge, 2)
            MICROGRID["battery_soc_pct"] = min(100, MICROGRID["battery_soc_pct"] + charge * 0.1)
            MICROGRID["grid_kw"] = round(net - charge, 2)
        else:
            MICROGRID["battery_kw"] = 0
            MICROGRID["grid_kw"] = round(net, 2)
    else:
        # 不足 -> 电池放电
        discharge = min(-net, 4.0)
        if MICROGRID["battery_soc_pct"] > 10:
            MICROGRID["battery_kw"] = round(-discharge, 2)
            MICROGRID["battery_soc_pct"] = max(0, MICROGRID["battery_soc_pct"] - discharge * 0.1)
            MICROGRID["grid_kw"] = round(-net - discharge, 2)
        else:
            MICROGRID["battery_kw"] = 0
            MICROGRID["grid_kw"] = round(-net, 2)
    MICROGRID["battery_soc_pct"] = round(MICROGRID["battery_soc_pct"], 1)


def get_energy_snapshot() -> dict:
    """获取能源快照"""
    _tick_microgrid()
    # 电网负载随机波动
    for r in GRID_REGIONS:
        r["load_pct"] = max(20, min(99, r["load_pct"] + random.randint(-3, 3)))
    total_load = sum(r["capacity_gw"] * r["load_pct"] / 100 for r in GRID_REGIONS)
    total_cap = sum(r["capacity_gw"] for r in GRID_REGIONS)
    avg_co2 = sum(e["pct"] * e["co2_g_per_kwh"] for e in ENERGY_MIX) / 100
    return {
        "module": "energy",
        "grid_regions": GRID_REGIONS,
        "energy_mix": ENERGY_MIX,
        "microgrid": MICROGRID,
        "global_load_gw": round(total_load, 1),
        "global_capacity_gw": total_cap,
        "global_load_pct": round(total_load / total_cap * 100, 1),
        "avg_co2_g_per_kwh": round(avg_co2, 1),
        "scanned_at": datetime.now().isoformat(),
    }

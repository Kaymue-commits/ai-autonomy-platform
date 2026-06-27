"""
能源监控模块 - 类似 ioBroker.energiefluss / solarsynkv3 / tplink-energy-monitor
全球能源结构、电网负载、光伏/储能流可视化
扩展: 全球水电站/光伏电站/核电站/天然气管道真实位置
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


# 全球主要水电站 (真实位置 + 装机容量)
HYDRO_PLANTS = [
    {"name": "三峡", "country": "中国", "lat": 30.82, "lon": 111.00, "capacity_mw": 22500, "river": "长江"},
    {"name": "白鹤滩", "country": "中国", "lat": 27.02, "lon": 102.79, "capacity_mw": 16000, "river": "金沙江"},
    {"name": "溪洛渡", "country": "中国", "lat": 28.25, "lon": 103.62, "capacity_mw": 13860, "river": "金沙江"},
    {"name": "伊泰普", "country": "巴西/巴拉圭", "lat": -25.42, "lon": -54.59, "capacity_mw": 14000, "river": "巴拉那河"},
    {"name": "古里", "country": "委内瑞拉", "lat": 6.78, "lon": -62.32, "capacity_mw": 10235, "river": "卡罗尼河"},
    {"name": "贝尔蒙蒂", "country": "巴西", "lat": -3.13, "lon": -52.20, "capacity_mw": 11233, "river": "兴谷河"},
    {"name": "乌东德", "country": "中国", "lat": 26.36, "lon": 102.62, "capacity_mw": 10200, "river": "金沙江"},
    {"name": "向家坝", "country": "中国", "lat": 28.65, "lon": 104.40, "capacity_mw": 7750, "river": "金沙江"},
    {"name": "大古力", "country": "美国", "lat": 47.59, "lon": -119.03, "capacity_mw": 6809, "river": "哥伦比亚河"},
    {"name": "萨扬舒申斯克", "country": "俄罗斯", "lat": 52.83, "lon": 91.41, "capacity_mw": 6400, "river": "叶尼塞河"},
    {"name": "克拉斯诺亚尔斯克", "country": "俄罗斯", "lat": 56.04, "lon": 92.49, "capacity_mw": 6000, "river": "叶尼塞河"},
    {"name": "努列克", "country": "塔吉克斯坦", "lat": 38.37, "lon": 69.34, "capacity_mw": 3015, "river": "瓦赫什河"},
]


# 全球主要核电站 (真实位置 + 装机容量)
NUCLEAR_PLANTS = [
    {"name": "柏崎刈羽", "country": "日本", "lat": 37.46, "lon": 138.62, "capacity_mw": 7965, "reactors": 7},
    {"name": "扎波罗热", "country": "乌克兰", "lat": 47.51, "lon": 34.59, "capacity_mw": 5700, "reactors": 6},
    {"name": "福岛第一", "country": "日本", "lat": 37.42, "lon": 141.03, "capacity_mw": 4696, "reactors": 6, "status": "退役"},
    {"name": "韩光", "country": "韩国", "lat": 35.41, "lon": 126.42, "capacity_mw": 5875, "reactors": 6},
    {"name": "岭澳", "country": "中国", "lat": 22.62, "lon": 114.55, "capacity_mw": 4148, "reactors": 4},
    {"name": "大亚湾", "country": "中国", "lat": 22.60, "lon": 114.55, "capacity_mw": 2938, "reactors": 2},
    {"name": "台山", "country": "中国", "lat": 21.93, "lon": 112.92, "capacity_mw": 3500, "reactors": 2},
    {"name": "布鲁斯", "country": "加拿大", "lat": 44.32, "lon": -81.59, "capacity_mw": 6430, "reactors": 8},
    {"name": "帕吕埃尔", "country": "法国", "lat": 49.74, "lon": 0.15, "capacity_mw": 5320, "reactors": 4},
    {"name": "卡特农", "country": "法国", "lat": 49.11, "lon": 6.27, "capacity_mw": 5200, "reactors": 4},
    {"name": "沃尔格勒", "country": "俄罗斯", "lat": 48.78, "lon": 44.50, "capacity_mw": 4000, "reactors": 4},
    {"name": "奥斯特罗韦涅茨", "country": "俄罗斯", "lat": 56.97, "lon": 33.13, "capacity_mw": 4200, "reactors": 4},
]


# 全球主要光伏电站 (真实位置 + 装机容量)
SOLAR_PLANTS = [
    {"name": "Bhadla太阳能园", "country": "印度", "lat": 27.50, "lon": 71.90, "capacity_mw": 2245, "type": "PV"},
    {"name": "Huanghe水电园", "country": "中国", "lat": 35.50, "lon": 100.20, "capacity_mw": 16200, "type": "光热+光伏"},
    {"name": "Benban", "country": "埃及", "lat": 23.88, "lon": 32.69, "capacity_mw": 1650, "type": "PV"},
    {"name": "Tengger沙漠", "country": "中国", "lat": 37.40, "lon": 105.10, "capacity_mw": 1547, "type": "PV"},
    {"name": "Noor阿布扎比", "country": "阿联酋", "lat": 24.08, "lon": 54.62, "capacity_mw": 1170, "type": "PV"},
    {"name": "Bhadla二期", "country": "印度", "lat": 27.50, "lon": 71.90, "capacity_mw": 1000, "type": "PV"},
    {"name": "Topaz", "country": "美国", "lat": 35.06, "lon": -120.08, "capacity_mw": 550, "type": "PV"},
    {"name": "SolarStar", "country": "美国", "lat": 34.84, "lon": -118.16, "capacity_mw": 579, "type": "PV"},
    {"name": "努奥-瓦尔扎扎特", "country": "摩洛哥", "lat": 31.05, "lon": -6.86, "capacity_mw": 580, "type": "光热CSP"},
    {"name": "Mohammed bin Rashid", "country": "阿联酋", "lat": 24.10, "lon": 55.40, "capacity_mw": 580, "type": "PV"},
    {"name": "迪尔克里克", "country": "美国", "lat": 30.62, "lon": -97.78, "capacity_mw": 500, "type": "PV"},
    {"name": "维拉纽瓦", "country": "墨西哥", "lat": 24.80, "lon": -101.50, "capacity_mw": 828, "type": "PV"},
]


# 全球主要风力发电场 (真实位置)
WIND_FARMS = [
    {"name": "甘肃风电基地", "country": "中国", "lat": 39.80, "lon": 96.40, "capacity_mw": 8000, "type": "陆上"},
    {"name": "GansuJiuquan", "country": "中国", "lat": 39.71, "lon": 98.49, "capacity_mw": 6000, "type": "陆上"},
    {"name": "Alta风能中心", "country": "美国", "lat": 35.02, "lon": -118.40, "capacity_mw": 1548, "type": "陆上"},
    {"name": "Hornsea", "country": "英国", "lat": 53.95, "lon": 2.20, "capacity_mw": 1218, "type": "海上"},
    {"name": "伦敦阵列", "country": "英国", "lat": 51.60, "lon": 1.70, "capacity_mw": 630, "type": "海上"},
    {"name": "Walney", "country": "英国", "lat": 54.05, "lon": -3.50, "capacity_mw": 659, "type": "海上"},
    {"name": "Gemini", "country": "荷兰", "lat": 54.00, "lon": 6.00, "capacity_mw": 600, "type": "海上"},
    {"name": "上海东海大桥", "country": "中国", "lat": 30.50, "lon": 122.20, "capacity_mw": 204, "type": "海上"},
]


# 全球主要天然气管道 (真实起止点, 用于地球可视化)
GAS_PIPELINES = [
    {"name": "北溪1号", "from": "俄罗斯维堡", "to": "德国格赖夫斯瓦尔德", "from_lat": 60.72, "from_lon": 28.74, "to_lat": 54.09, "to_lon": 13.51, "length_km": 1224, "capacity_bcm_y": 55},
    {"name": "北溪2号", "from": "俄罗斯维堡", "to": "德国格赖夫斯瓦尔德", "from_lat": 60.72, "from_lon": 28.74, "to_lat": 54.09, "to_lon": 13.51, "length_km": 1230, "capacity_bcm_y": 55},
    {"name": "中亚-中国", "from": "土库曼斯坦", "to": "中国新疆", "from_lat": 38.00, "from_lon": 58.50, "to_lat": 43.80, "to_lon": 87.60, "length_km": 1833, "capacity_bcm_y": 55},
    {"name": "Power of Siberia", "from": "俄罗斯科维克塔", "to": "中国黑河", "from_lat": 54.50, "from_lon": 104.50, "to_lat": 50.20, "to_lon": 127.50, "length_km": 3871, "capacity_bcm_y": 38},
    {"name": "兰溪-永福", "from": "缅甸皎漂", "to": "中国瑞丽", "from_lat": 19.62, "from_lon": 93.55, "to_lat": 24.00, "to_lon": 97.80, "length_km": 793, "capacity_bcm_y": 12},
    {"name": "TurkStream", "from": "俄罗斯", "to": "土耳其", "from_lat": 45.20, "from_lon": 36.60, "to_lat": 41.30, "to_lon": 31.50, "length_km": 930, "capacity_bcm_y": 31.5},
    {"name": "亚马尔-欧洲", "from": "俄罗斯", "to": "德国", "from_lat": 66.50, "from_lon": 66.50, "to_lat": 52.50, "to_lon": 13.40, "length_km": 4107, "capacity_bcm_y": 33},
    {"name": "蓝溪", "from": "俄罗斯", "to": "土耳其", "from_lat": 45.20, "from_lon": 36.60, "to_lat": 41.20, "to_lon": 31.50, "length_km": 1213, "capacity_bcm_y": 16},
    {"name": "LNG卡塔尔-中国", "from": "卡塔尔", "to": "中国", "from_lat": 25.30, "from_lon": 51.50, "to_lat": 31.20, "to_lon": 121.50, "length_km": 8500, "capacity_bcm_y": 70, "type": "LNG海运"},
    {"name": "页岩气美国-欧洲", "from": "美国", "to": "欧洲", "from_lat": 29.00, "from_lon": -90.00, "to_lat": 50.00, "to_lon": 0.00, "length_km": 7500, "capacity_bcm_y": 50, "type": "LNG海运"},
]


# 单个家庭/工业微电网模拟（参考 energiefluss-erweitert 风格）
MICROGRID = {
    "solar_kw": 12.5,
    "solar_peak_kw": 15.0,
    "battery_soc_pct": 68,
    "battery_kw": 3.2,
    "grid_kw": -1.8,
    "home_load_kw": 4.5,
    "ev_charging_kw": 0,
    "ev_connected": False,
}


def _tick_microgrid():
    """模拟微电网状态变化"""
    hour = datetime.now().hour
    if 6 <= hour <= 18:
        factor = max(0, 1 - abs(hour - 12) / 6) + random.uniform(-0.1, 0.1)
        MICROGRID["solar_kw"] = round(max(0, MICROGRID["solar_peak_kw"] * factor), 2)
    else:
        MICROGRID["solar_kw"] = 0.0
    solar = MICROGRID["solar_kw"]
    home = MICROGRID["home_load_kw"] + random.uniform(-0.5, 0.5)
    MICROGRID["home_load_kw"] = round(home, 2)
    net = solar - home
    if net > 0:
        charge = min(net, 5.0)
        if MICROGRID["battery_soc_pct"] < 95:
            MICROGRID["battery_kw"] = round(charge, 2)
            MICROGRID["battery_soc_pct"] = min(100, MICROGRID["battery_soc_pct"] + charge * 0.1)
            MICROGRID["grid_kw"] = round(net - charge, 2)
        else:
            MICROGRID["battery_kw"] = 0
            MICROGRID["grid_kw"] = round(net, 2)
    else:
        discharge = min(-net, 4.0)
        if MICROGRID["battery_soc_pct"] > 10:
            MICROGRID["battery_kw"] = round(-discharge, 2)
            MICROGRID["battery_soc_pct"] = max(0, MICROGRID["battery_soc_pct"] - discharge * 0.1)
            MICROGRID["grid_kw"] = round(-net - discharge, 2)
        else:
            MICROGRID["battery_kw"] = 0
            MICROGRID["grid_kw"] = round(-net, 2)
    MICROGRID["battery_soc_pct"] = round(MICROGRID["battery_soc_pct"], 1)


def _tick_facilities():
    """模拟设施实时出力波动"""
    # 水电站出力受季节影响 (简化随机波动)
    for h in HYDRO_PLANTS:
        h["current_pct"] = max(30, min(100, 75 + random.randint(-15, 15)))
    # 核电站稳定 85-95%
    for n in NUCLEAR_PLANTS:
        n["current_pct"] = max(70, min(100, 88 + random.randint(-8, 8)))
    # 光伏看时间 (白天才发电)
    hour = datetime.now().hour
    if 6 <= hour <= 18:
        solar_factor = max(0, 1 - abs(hour - 12) / 6) + random.uniform(-0.1, 0.1)
    else:
        solar_factor = 0
    for s in SOLAR_PLANTS:
        s["current_pct"] = round(max(0, min(100, solar_factor * 100 + random.uniform(-5, 5))), 1)
    # 风电随机
    for w in WIND_FARMS:
        w["current_pct"] = max(10, min(100, 60 + random.randint(-25, 25)))


def get_energy_snapshot() -> dict:
    """获取能源快照"""
    _tick_microgrid()
    _tick_facilities()
    for r in GRID_REGIONS:
        r["load_pct"] = max(20, min(99, r["load_pct"] + random.randint(-3, 3)))
    total_load = sum(r["capacity_gw"] * r["load_pct"] / 100 for r in GRID_REGIONS)
    total_cap = sum(r["capacity_gw"] for r in GRID_REGIONS)
    avg_co2 = sum(e["pct"] * e["co2_g_per_kwh"] for e in ENERGY_MIX) / 100
    # 汇总设施统计
    total_hydro_mw = sum(h["capacity_mw"] for h in HYDRO_PLANTS)
    total_nuclear_mw = sum(n["capacity_mw"] for n in NUCLEAR_PLANTS)
    total_solar_mw = sum(s["capacity_mw"] for s in SOLAR_PLANTS)
    total_wind_mw = sum(w["capacity_mw"] for w in WIND_FARMS)
    return {
        "module": "energy",
        "grid_regions": GRID_REGIONS,
        "energy_mix": ENERGY_MIX,
        "microgrid": MICROGRID,
        "facilities": {
            "hydro": HYDRO_PLANTS,
            "nuclear": NUCLEAR_PLANTS,
            "solar": SOLAR_PLANTS,
            "wind": WIND_FARMS,
            "gas_pipelines": GAS_PIPELINES,
        },
        "totals": {
            "hydro_mw": total_hydro_mw,
            "nuclear_mw": total_nuclear_mw,
            "solar_mw": total_solar_mw,
            "wind_mw": total_wind_mw,
            "hydro_count": len(HYDRO_PLANTS),
            "nuclear_count": len(NUCLEAR_PLANTS),
            "solar_count": len(SOLAR_PLANTS),
            "wind_count": len(WIND_FARMS),
            "gas_pipeline_count": len(GAS_PIPELINES),
            "gas_pipeline_total_km": sum(p["length_km"] for p in GAS_PIPELINES),
        },
        "global_load_gw": round(total_load, 1),
        "global_capacity_gw": total_cap,
        "global_load_pct": round(total_load / total_cap * 100, 1),
        "avg_co2_g_per_kwh": round(avg_co2, 1),
        "scanned_at": datetime.now().isoformat(),
    }


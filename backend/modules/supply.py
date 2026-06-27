"""
全球供应链模块 - 全球港口、海运航道、航空货运、陆运枢纽可视化
扩展: 全球主要港口/航道/航空枢纽/陆运口岸真实位置
"""
import random
from datetime import datetime


# 全球主要港口 (25个, 真实经纬度)
PORTS = [
    {"name": "上海港", "country": "中国", "lat": 31.23, "lon": 121.47, "teu_million": 47.3, "type": "container", "busy_pct": 92, "risk_level": "low"},
    {"name": "新加坡港", "country": "新加坡", "lat": 1.35, "lon": 103.82, "teu_million": 39.0, "type": "container", "busy_pct": 88, "risk_level": "low"},
    {"name": "宁波-舟山港", "country": "中国", "lat": 29.87, "lon": 121.83, "teu_million": 33.4, "type": "container", "busy_pct": 85, "risk_level": "low"},
    {"name": "深圳港", "country": "中国", "lat": 22.54, "lon": 114.06, "teu_million": 28.8, "type": "container", "busy_pct": 86, "risk_level": "low"},
    {"name": "青岛港", "country": "中国", "lat": 36.07, "lon": 120.28, "teu_million": 25.7, "type": "container", "busy_pct": 80, "risk_level": "low"},
    {"name": "广州港", "country": "中国", "lat": 23.13, "lon": 113.27, "teu_million": 24.4, "type": "container", "busy_pct": 78, "risk_level": "low"},
    {"name": "釜山港", "country": "韩国", "lat": 35.10, "lon": 129.04, "teu_million": 23.2, "type": "container", "busy_pct": 75, "risk_level": "low"},
    {"name": "天津港", "country": "中国", "lat": 38.97, "lon": 117.74, "teu_million": 21.0, "type": "container", "busy_pct": 72, "risk_level": "medium"},
    {"name": "鹿特丹港", "country": "荷兰", "lat": 51.92, "lon": 4.48, "teu_million": 15.3, "type": "container", "busy_pct": 70, "risk_level": "low"},
    {"name": "香港港", "country": "中国香港", "lat": 22.32, "lon": 114.17, "teu_million": 14.7, "type": "container", "busy_pct": 68, "risk_level": "medium"},
    {"name": "洛杉矶港", "country": "美国", "lat": 33.74, "lon": -118.26, "teu_million": 10.7, "type": "container", "busy_pct": 75, "risk_level": "medium"},
    {"name": "汉堡港", "country": "德国", "lat": 53.55, "lon": 9.99, "teu_million": 8.3, "type": "container", "busy_pct": 65, "risk_level": "low"},
    {"name": "迪拜港", "country": "阿联酋", "lat": 25.25, "lon": 55.28, "teu_million": 18.6, "type": "container", "busy_pct": 82, "risk_level": "medium"},
    {"name": "纽约港", "country": "美国", "lat": 40.68, "lon": -74.04, "teu_million": 9.5, "type": "container", "busy_pct": 70, "risk_level": "low"},
    {"name": "新奥尔良港", "country": "美国", "lat": 29.94, "lon": -90.07, "teu_million": 0.8, "type": "bulk", "busy_pct": 60, "risk_level": "low"},
    {"name": "东京港", "country": "日本", "lat": 35.65, "lon": 139.84, "teu_million": 4.4, "type": "container", "busy_pct": 62, "risk_level": "low"},
    {"name": "高雄港", "country": "中国台湾", "lat": 22.62, "lon": 120.28, "teu_million": 9.9, "type": "container", "busy_pct": 65, "risk_level": "medium"},
    {"name": "安特卫普港", "country": "比利时", "lat": 51.22, "lon": 4.40, "teu_million": 12.1, "type": "container", "busy_pct": 68, "risk_level": "low"},
    {"name": "巴生港", "country": "马来西亚", "lat": 3.00, "lon": 101.40, "teu_million": 13.8, "type": "container", "busy_pct": 70, "risk_level": "low"},
    {"name": "丹戎帕拉帕斯港", "country": "马来西亚", "lat": 1.36, "lon": 103.55, "teu_million": 9.6, "type": "container", "busy_pct": 60, "risk_level": "low"},
    {"name": "悉尼港", "country": "澳大利亚", "lat": -33.87, "lon": 151.21, "teu_million": 2.6, "type": "container", "busy_pct": 55, "risk_level": "low"},
    {"name": "里约热内卢港", "country": "巴西", "lat": -22.90, "lon": -43.18, "teu_million": 1.2, "type": "mixed", "busy_pct": 50, "risk_level": "medium"},
    {"name": "开普敦港", "country": "南非", "lat": -33.92, "lon": 18.42, "teu_million": 1.0, "type": "mixed", "busy_pct": 48, "risk_level": "medium"},
    {"name": "孟买港", "country": "印度", "lat": 19.08, "lon": 72.88, "teu_million": 4.8, "type": "container", "busy_pct": 65, "risk_level": "medium"},
    {"name": "伊斯坦布尔港", "country": "土耳其", "lat": 41.01, "lon": 28.98, "teu_million": 3.2, "type": "mixed", "busy_pct": 58, "risk_level": "high"},
]


# 全球主要海运航道 (12条, 真实起止点)
SHIPPING_LANES = [
    {"name": "马六甲海峡", "from_lat": 2.20, "from_lon": 101.20, "to_lat": 6.50, "to_lon": 99.70, "importance": "critical", "traffic_pct": 95, "risk_level": "medium", "cargo_type": "mixed"},
    {"name": "苏伊士运河", "from_lat": 30.70, "from_lon": 32.40, "to_lat": 29.90, "to_lon": 32.55, "importance": "critical", "traffic_pct": 88, "risk_level": "high", "cargo_type": "mixed"},
    {"name": "巴拿马运河", "from_lat": 9.40, "from_lon": -79.95, "to_lat": 9.30, "to_lon": -79.00, "importance": "high", "traffic_pct": 75, "risk_level": "medium", "cargo_type": "container"},
    {"name": "霍尔木兹海峡", "from_lat": 26.70, "from_lon": 56.50, "to_lat": 25.70, "to_lon": 55.80, "importance": "critical", "traffic_pct": 90, "risk_level": "high", "cargo_type": "oil"},
    {"name": "直布罗陀海峡", "from_lat": 35.90, "from_lon": -5.40, "to_lat": 36.00, "to_lon": -5.30, "importance": "high", "traffic_pct": 72, "risk_level": "low", "cargo_type": "mixed"},
    {"name": "好望角航线", "from_lat": -33.90, "from_lon": 18.40, "to_lat": -34.35, "to_lon": 21.20, "importance": "high", "traffic_pct": 60, "risk_level": "medium", "cargo_type": "mixed"},
    {"name": "北太平洋航线", "from_lat": 35.70, "from_lon": 140.90, "to_lat": 34.05, "to_lon": -118.25, "importance": "critical", "traffic_pct": 85, "risk_level": "low", "cargo_type": "container"},
    {"name": "北大西洋航线", "from_lat": 51.92, "from_lon": 4.48, "to_lat": 40.68, "to_lon": -74.04, "importance": "high", "traffic_pct": 78, "risk_level": "low", "cargo_type": "container"},
    {"name": "印度洋航线", "from_lat": 1.35, "from_lon": 103.82, "to_lat": 25.25, "to_lon": 55.28, "importance": "high", "traffic_pct": 70, "risk_level": "medium", "cargo_type": "mixed"},
    {"name": "地中海航线", "from_lat": 36.00, "from_lon": -5.30, "to_lat": 30.70, "to_lon": 32.40, "importance": "high", "traffic_pct": 68, "risk_level": "medium", "cargo_type": "mixed"},
    {"name": "南中国海航线", "from_lat": 22.32, "from_lon": 114.17, "to_lat": 1.35, "to_lon": 103.82, "importance": "critical", "traffic_pct": 92, "risk_level": "high", "cargo_type": "mixed"},
    {"name": "波罗的海航线", "from_lat": 53.55, "from_lon": 9.99, "to_lat": 59.93, "to_lon": 30.34, "importance": "medium", "traffic_pct": 55, "risk_level": "low", "cargo_type": "bulk"},
]


# 全球主要航空货运枢纽 (10个, 真实经纬度)
AIR_HUBS = [
    {"name": "香港国际机场", "city": "香港", "country": "中国", "lat": 22.31, "lon": 113.91, "cargo_tonnage": 420, "rank": 1},
    {"name": "孟菲斯国际机场", "city": "孟菲斯", "country": "美国", "lat": 35.04, "lon": -89.98, "cargo_tonnage": 410, "rank": 2},
    {"name": "上海浦东国际机场", "city": "上海", "country": "中国", "lat": 31.14, "lon": 121.80, "cargo_tonnage": 398, "rank": 3},
    {"name": "安克雷奇国际机场", "city": "安克雷奇", "country": "美国", "lat": 61.17, "lon": -149.99, "cargo_tonnage": 280, "rank": 4},
    {"name": "仁川国际机场", "city": "首尔", "country": "韩国", "lat": 37.46, "lon": 126.44, "cargo_tonnage": 276, "rank": 5},
    {"name": "法兰克福机场", "city": "法兰克福", "country": "德国", "lat": 50.03, "lon": 8.57, "cargo_tonnage": 230, "rank": 6},
    {"name": "新加坡樟宜机场", "city": "新加坡", "country": "新加坡", "lat": 1.36, "lon": 103.99, "cargo_tonnage": 210, "rank": 7},
    {"name": "迪拜国际机场", "city": "迪拜", "country": "阿联酋", "lat": 25.25, "lon": 55.36, "cargo_tonnage": 205, "rank": 8},
    {"name": "路易斯维尔国际机场", "city": "路易斯维尔", "country": "美国", "lat": 38.17, "lon": -85.74, "cargo_tonnage": 185, "rank": 9},
    {"name": "东京成田国际机场", "city": "东京", "country": "日本", "lat": 35.77, "lon": 140.39, "cargo_tonnage": 175, "rank": 10},
]


# 全球主要陆运枢纽/铁路口岸 (8个, 真实经纬度)
LAND_HUBS = [
    {"name": "阿拉山口口岸", "country": "中国", "lat": 45.18, "lon": 82.57, "type": "rail", "throughput_pct": 85},
    {"name": "满洲里口岸", "country": "中国", "lat": 49.58, "lon": 117.42, "type": "border", "throughput_pct": 78},
    {"name": "二连浩特口岸", "country": "中国", "lat": 43.65, "lon": 112.00, "type": "border", "throughput_pct": 70},
    {"name": "马拉舍维奇", "country": "波兰", "lat": 52.03, "lon": 23.28, "type": "rail", "throughput_pct": 82},
    {"name": "罗兹", "country": "波兰", "lat": 51.76, "lon": 19.46, "type": "rail", "throughput_pct": 75},
    {"name": "汉堡陆港", "country": "德国", "lat": 53.55, "lon": 9.99, "type": "truck", "throughput_pct": 72},
    {"name": "重庆果园港", "country": "中国", "lat": 29.68, "lon": 106.98, "type": "rail", "throughput_pct": 78},
    {"name": "西安国际港务区", "country": "中国", "lat": 34.28, "lon": 108.96, "type": "rail", "throughput_pct": 80},
]


def _tick_ports():
    """模拟港口繁忙度波动"""
    for p in PORTS:
        p["busy_pct"] = max(30, min(99, p["busy_pct"] + random.randint(-5, 5)))


def _tick_lanes():
    """模拟航道交通量波动"""
    for l in SHIPPING_LANES:
        l["traffic_pct"] = max(20, min(99, l["traffic_pct"] + random.randint(-4, 4)))


def _tick_air_hubs():
    """模拟航空货运量波动"""
    for a in AIR_HUBS:
        change = random.uniform(-0.05, 0.05)
        a["cargo_tonnage"] = round(max(50, a["cargo_tonnage"] * (1 + change)), 1)


def _tick_land_hubs():
    """模拟陆运枢纽吞吐量波动"""
    for h in LAND_HUBS:
        h["throughput_pct"] = max(20, min(99, h["throughput_pct"] + random.randint(-5, 5)))


def get_supply_snapshot() -> dict:
    """获取全球供应链快照"""
    _tick_ports()
    _tick_lanes()
    _tick_air_hubs()
    _tick_land_hubs()

    total_ports = len(PORTS)
    total_lanes = len(SHIPPING_LANES)
    total_air_hubs = len(AIR_HUBS)
    total_land_hubs = len(LAND_HUBS)

    total_teu = sum(p["teu_million"] for p in PORTS)
    avg_port_busy = sum(p["busy_pct"] for p in PORTS) / total_ports
    avg_lane_traffic = sum(l["traffic_pct"] for l in SHIPPING_LANES) / total_lanes
    total_air_cargo = sum(a["cargo_tonnage"] for a in AIR_HUBS)
    avg_land_throughput = sum(h["throughput_pct"] for h in LAND_HUBS) / total_land_hubs

    global_trade_index = round((avg_port_busy * 0.4 + avg_lane_traffic * 0.3 + avg_land_throughput * 0.15 + (total_air_cargo / 25) * 0.15), 1)

    return {
        "module": "supply",
        "ports": PORTS,
        "shipping_lanes": SHIPPING_LANES,
        "air_hubs": AIR_HUBS,
        "land_hubs": LAND_HUBS,
        "total_ports": total_ports,
        "total_lanes": total_lanes,
        "total_air_hubs": total_air_hubs,
        "total_land_hubs": total_land_hubs,
        "global_trade_index": global_trade_index,
        "totals": {
            "total_teu_million": round(total_teu, 1),
            "total_air_cargo_kt": round(total_air_cargo, 1),
            "avg_port_busy_pct": round(avg_port_busy, 1),
            "avg_lane_traffic_pct": round(avg_lane_traffic, 1),
            "avg_land_throughput_pct": round(avg_land_throughput, 1),
        },
        "scanned_at": datetime.now().isoformat(),
    }

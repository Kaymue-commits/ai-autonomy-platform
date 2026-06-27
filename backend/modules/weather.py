"""
气象海洋模块 - 全球气象数据实时模拟
全球气旋/台风、洋流、云层带、气象站数据可视化
扩展: 真实经纬度位置 + 模拟实时波动
"""
import random
from datetime import datetime


# 全球主要气旋/台风 (真实位置分布)
CYCLONES = [
    {
        "name": "台风玛莉亚",
        "lat": 18.5, "lon": 132.3,
        "category": "超强台风",
        "wind_kmh": 215, "pressure": 915,
        "movement_dir": "西北偏西",
        "affected_area": "西北太平洋"
    },
    {
        "name": "台风山神",
        "lat": 12.8, "lon": 145.2,
        "category": "强台风",
        "wind_kmh": 175, "pressure": 945,
        "movement_dir": "西北",
        "affected_area": "西北太平洋"
    },
    {
        "name": "飓风厄玛",
        "lat": 25.3, "lon": -72.5,
        "category": "五级飓风",
        "wind_kmh": 260, "pressure": 914,
        "movement_dir": "西北偏北",
        "affected_area": "北大西洋加勒比"
    },
    {
        "name": "飓风哈维",
        "lat": 19.8, "lon": -95.2,
        "category": "四级飓风",
        "wind_kmh": 210, "pressure": 937,
        "movement_dir": "西北",
        "affected_area": "北大西洋墨西哥湾"
    },
    {
        "name": "气旋法尼",
        "lat": 14.2, "lon": 86.5,
        "category": "极强气旋",
        "wind_kmh": 215, "pressure": 932,
        "movement_dir": "东北偏北",
        "affected_area": "北印度洋孟加拉湾"
    },
    {
        "name": "气旋穆查",
        "lat": 12.5, "lon": 90.8,
        "category": "特强气旋",
        "wind_kmh": 195, "pressure": 942,
        "movement_dir": "东北",
        "affected_area": "北印度洋孟加拉湾"
    },
    {
        "name": "热带气旋特雷弗",
        "lat": -12.6, "lon": 142.3,
        "category": "三级热带气旋",
        "wind_kmh": 150, "pressure": 960,
        "movement_dir": "东南偏南",
        "affected_area": "澳大利亚海域"
    },
    {
        "name": "气旋弗雷迪",
        "lat": -18.5, "lon": 65.2,
        "category": "强热带气旋",
        "wind_kmh": 185, "pressure": 940,
        "movement_dir": "西南偏西",
        "affected_area": "南印度洋"
    },
]


# 全球主要洋流 (真实起止点)
OCEAN_CURRENTS = [
    {
        "name": "湾流",
        "from_lat": 25.0, "from_lon": -75.0,
        "to_lat": 55.0, "to_lon": -20.0,
        "speed_kt": 4.5, "temp_c": 24.0,
        "type": "warm"
    },
    {
        "name": "黑潮",
        "from_lat": 10.0, "from_lon": 130.0,
        "to_lat": 40.0, "to_lon": 160.0,
        "speed_kt": 3.8, "temp_c": 22.0,
        "type": "warm"
    },
    {
        "name": "北太平洋暖流",
        "from_lat": 35.0, "from_lon": 150.0,
        "to_lat": 45.0, "to_lon": -130.0,
        "speed_kt": 1.2, "temp_c": 16.0,
        "type": "warm"
    },
    {
        "name": "秘鲁寒流",
        "from_lat": -5.0, "from_lon": -80.0,
        "to_lat": -35.0, "to_lon": -110.0,
        "speed_kt": 1.5, "temp_c": 14.0,
        "type": "cold"
    },
    {
        "name": "本格拉寒流",
        "from_lat": 15.0, "from_lon": 12.0,
        "to_lat": -30.0, "to_lon": 15.0,
        "speed_kt": 1.0, "temp_c": 16.0,
        "type": "cold"
    },
    {
        "name": "加利福尼亚寒流",
        "from_lat": 40.0, "from_lon": -125.0,
        "to_lat": 15.0, "to_lon": -110.0,
        "speed_kt": 1.2, "temp_c": 18.0,
        "type": "cold"
    },
    {
        "name": "加那利寒流",
        "from_lat": 45.0, "from_lon": -10.0,
        "to_lat": 10.0, "to_lon": -20.0,
        "speed_kt": 0.8, "temp_c": 20.0,
        "type": "cold"
    },
    {
        "name": "巴西暖流",
        "from_lat": 10.0, "from_lon": -35.0,
        "to_lat": -30.0, "to_lon": -50.0,
        "speed_kt": 1.8, "temp_c": 26.0,
        "type": "warm"
    },
    {
        "name": "莫桑比克暖流",
        "from_lat": 5.0, "from_lon": 50.0,
        "to_lat": -30.0, "to_lon": 35.0,
        "speed_kt": 2.0, "temp_c": 25.0,
        "type": "warm"
    },
    {
        "name": "西风漂流",
        "from_lat": -40.0, "from_lon": 0.0,
        "to_lat": -55.0, "to_lon": 360.0,
        "speed_kt": 1.5, "temp_c": 5.0,
        "type": "cold"
    },
    {
        "name": "东澳大利亚暖流",
        "from_lat": 10.0, "from_lon": 155.0,
        "to_lat": -35.0, "to_lon": 150.0,
        "speed_kt": 1.8, "temp_c": 23.0,
        "type": "warm"
    },
    {
        "name": "赤道暖流",
        "from_lat": 0.0, "from_lon": -80.0,
        "to_lat": 0.0, "to_lon": -20.0,
        "speed_kt": 2.5, "temp_c": 28.0,
        "type": "warm"
    },
]


# 全球主要云层带
CLOUD_BELTS = [
    {
        "name": "赤道辐合带",
        "lat_center": 0.0, "lon_range": [0.0, 360.0],
        "coverage_pct": 75, "cloud_type": "积雨云"
    },
    {
        "name": "北副热带高压带",
        "lat_center": 30.0, "lon_range": [0.0, 360.0],
        "coverage_pct": 25, "cloud_type": "层积云"
    },
    {
        "name": "南副热带高压带",
        "lat_center": -30.0, "lon_range": [0.0, 360.0],
        "coverage_pct": 28, "cloud_type": "层积云"
    },
    {
        "name": "北极锋区云带",
        "lat_center": 60.0, "lon_range": [0.0, 360.0],
        "coverage_pct": 60, "cloud_type": "雨层云"
    },
    {
        "name": "南极锋区云带",
        "lat_center": -60.0, "lon_range": [0.0, 360.0],
        "coverage_pct": 65, "cloud_type": "雨层云"
    },
    {
        "name": "热带辐合云带",
        "lat_center": 10.0, "lon_range": [-180.0, 180.0],
        "coverage_pct": 70, "cloud_type": "积云"
    },
]


# 全球主要气象站点 (20个，分布各大洲)
WEATHER_STATIONS = [
    {"name": "北京", "country": "中国", "lat": 39.90, "lon": 116.40, "temp_c": 22.5, "humidity_pct": 65, "pressure_hpa": 1013, "condition": "晴", "wind_kmh": 12},
    {"name": "上海", "country": "中国", "lat": 31.23, "lon": 121.47, "temp_c": 25.8, "humidity_pct": 78, "pressure_hpa": 1010, "condition": "多云", "wind_kmh": 18},
    {"name": "东京", "country": "日本", "lat": 35.68, "lon": 139.69, "temp_c": 24.2, "humidity_pct": 72, "pressure_hpa": 1008, "condition": "小雨", "wind_kmh": 15},
    {"name": "新加坡", "country": "新加坡", "lat": 1.35, "lon": 103.82, "temp_c": 29.5, "humidity_pct": 85, "pressure_hpa": 1011, "condition": "雷阵雨", "wind_kmh": 8},
    {"name": "悉尼", "country": "澳大利亚", "lat": -33.87, "lon": 151.21, "temp_c": 18.3, "humidity_pct": 68, "pressure_hpa": 1015, "condition": "晴", "wind_kmh": 22},
    {"name": "新德里", "country": "印度", "lat": 28.61, "lon": 77.21, "temp_c": 38.5, "humidity_pct": 35, "pressure_hpa": 1000, "condition": "晴", "wind_kmh": 10},
    {"name": "迪拜", "country": "阿联酋", "lat": 25.20, "lon": 55.27, "temp_c": 41.2, "humidity_pct": 28, "pressure_hpa": 1005, "condition": "晴", "wind_kmh": 16},
    {"name": "莫斯科", "country": "俄罗斯", "lat": 55.75, "lon": 37.62, "temp_c": 15.8, "humidity_pct": 58, "pressure_hpa": 1018, "condition": "多云", "wind_kmh": 14},
    {"name": "伦敦", "country": "英国", "lat": 51.51, "lon": -0.13, "temp_c": 14.2, "humidity_pct": 75, "pressure_hpa": 1016, "condition": "阴", "wind_kmh": 20},
    {"name": "巴黎", "country": "法国", "lat": 48.86, "lon": 2.35, "temp_c": 16.5, "humidity_pct": 62, "pressure_hpa": 1014, "condition": "晴间多云", "wind_kmh": 17},
    {"name": "纽约", "country": "美国", "lat": 40.71, "lon": -74.01, "temp_c": 21.8, "humidity_pct": 60, "pressure_hpa": 1012, "condition": "晴", "wind_kmh": 19},
    {"name": "洛杉矶", "country": "美国", "lat": 34.05, "lon": -118.24, "temp_c": 24.5, "humidity_pct": 45, "pressure_hpa": 1013, "condition": "晴", "wind_kmh": 8},
    {"name": "圣保罗", "country": "巴西", "lat": -23.55, "lon": -46.63, "temp_c": 20.2, "humidity_pct": 70, "pressure_hpa": 1015, "condition": "多云", "wind_kmh": 13},
    {"name": "开罗", "country": "埃及", "lat": 30.04, "lon": 31.24, "temp_c": 35.8, "humidity_pct": 30, "pressure_hpa": 1008, "condition": "晴", "wind_kmh": 12},
    {"name": "开普敦", "country": "南非", "lat": -33.92, "lon": 18.42, "temp_c": 16.5, "humidity_pct": 65, "pressure_hpa": 1016, "condition": "多云", "wind_kmh": 25},
    {"name": "雷克雅未克", "country": "冰岛", "lat": 64.15, "lon": -21.94, "temp_c": 8.2, "humidity_pct": 80, "pressure_hpa": 1005, "condition": "小雨", "wind_kmh": 30},
    {"name": "夏威夷", "country": "美国", "lat": 21.31, "lon": -157.86, "temp_c": 27.5, "humidity_pct": 75, "pressure_hpa": 1010, "condition": "晴", "wind_kmh": 22},
    {"name": "香港", "country": "中国", "lat": 22.32, "lon": 114.17, "temp_c": 28.8, "humidity_pct": 82, "pressure_hpa": 1007, "condition": "雷阵雨", "wind_kmh": 20},
    {"name": "墨西哥城", "country": "墨西哥", "lat": 19.43, "lon": -99.13, "temp_c": 18.5, "humidity_pct": 55, "pressure_hpa": 1025, "condition": "晴间多云", "wind_kmh": 10},
    {"name": "伊斯坦布尔", "country": "土耳其", "lat": 41.01, "lon": 28.98, "temp_c": 22.0, "humidity_pct": 60, "pressure_hpa": 1012, "condition": "晴", "wind_kmh": 15},
]


def _tick_cyclones():
    """模拟气旋移动和强度波动"""
    for c in CYCLONES:
        c["wind_kmh"] = round(max(80, min(300, c["wind_kmh"] + random.uniform(-8, 8))), 0)
        c["pressure"] = round(max(880, min(1000, c["pressure"] + random.uniform(-3, 3))), 0)
        c["lat"] = round(c["lat"] + random.uniform(-0.8, 0.8), 1)
        c["lon"] = round(c["lon"] + random.uniform(-0.8, 0.8), 1)
        wind = c["wind_kmh"]
        if wind >= 250:
            c["category"] = "五级飓风"
        elif wind >= 210:
            c["category"] = "四级飓风"
        elif wind >= 175:
            c["category"] = "强台风"
        elif wind >= 150:
            c["category"] = "台风"
        elif wind >= 120:
            c["category"] = "强热带风暴"
        else:
            c["category"] = "热带风暴"


def _tick_weather_stations():
    """模拟气象站数据波动"""
    conditions = ["晴", "晴间多云", "多云", "阴", "小雨", "中雨", "雷阵雨"]
    for s in WEATHER_STATIONS:
        s["temp_c"] = round(max(-20, min(50, s["temp_c"] + random.uniform(-1.5, 1.5))), 1)
        s["humidity_pct"] = round(max(10, min(95, s["humidity_pct"] + random.uniform(-5, 5))), 0)
        s["pressure_hpa"] = round(max(980, min(1040, s["pressure_hpa"] + random.uniform(-2, 2))), 0)
        s["wind_kmh"] = round(max(0, min(60, s["wind_kmh"] + random.uniform(-3, 3))), 0)
        if random.random() < 0.1:
            s["condition"] = random.choice(conditions)


def _tick_cloud_belts():
    """模拟云层覆盖率波动"""
    for cb in CLOUD_BELTS:
        cb["coverage_pct"] = round(max(5, min(95, cb["coverage_pct"] + random.uniform(-3, 3))), 0)


def _tick_ocean_currents():
    """模拟洋流速度和温度波动"""
    for oc in OCEAN_CURRENTS:
        oc["speed_kt"] = round(max(0.2, min(6.0, oc["speed_kt"] + random.uniform(-0.3, 0.3))), 1)
        oc["temp_c"] = round(max(-2, min(30, oc["temp_c"] + random.uniform(-0.8, 0.8))), 1)


def get_weather_snapshot() -> dict:
    """获取气象快照"""
    _tick_cyclones()
    _tick_ocean_currents()
    _tick_cloud_belts()
    _tick_weather_stations()

    avg_temp = round(sum(s["temp_c"] for s in WEATHER_STATIONS) / len(WEATHER_STATIONS), 1)
    avg_humidity = round(sum(s["humidity_pct"] for s in WEATHER_STATIONS) / len(WEATHER_STATIONS), 0)

    return {
        "module": "weather",
        "cyclones": CYCLONES,
        "ocean_currents": OCEAN_CURRENTS,
        "cloud_belts": CLOUD_BELTS,
        "weather_stations": WEATHER_STATIONS,
        "global_avg_temp": avg_temp,
        "global_avg_humidity": avg_humidity,
        "total_cyclones": len(CYCLONES),
        "total_ocean_currents": len(OCEAN_CURRENTS),
        "total_cloud_belts": len(CLOUD_BELTS),
        "total_weather_stations": len(WEATHER_STATIONS),
        "scanned_at": datetime.now().isoformat(),
    }

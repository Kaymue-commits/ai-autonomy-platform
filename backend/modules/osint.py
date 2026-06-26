"""
OSINT冲突追踪模块 - 类似 war-map / OSINT-War-Room / n01d-overwatch / crisismap
全球冲突热点、军事调动、网络战、ACLED风格事件流
"""
import random
from datetime import datetime, timedelta


# 全球冲突热点（基于公开 OSINT 数据，参考 war-map / crisismap）
CONFLICT_HOTSPOTS = [
    {
        "id": "ukr-east",
        "name": "乌克兰东部",
        "lat": 48.5, "lon": 38.0,
        "intensity": 95,
        "category": "active_conflict",
        "actors": ["俄军", "乌军"],
        "events_today": 42,
        "last_event": "炮击顿涅茨克方向",
    },
    {
        "id": "gaza",
        "name": "加沙地带",
        "lat": 31.4, "lon": 34.4,
        "intensity": 92,
        "category": "active_conflict",
        "actors": ["IDF", "哈马斯"],
        "events_today": 38,
        "last_event": "空袭北部城镇",
    },
    {
        "id": "red-sea",
        "name": "红海/曼德海峡",
        "lat": 13.5, "lon": 43.0,
        "intensity": 75,
        "category": "maritime",
        "actors": ["胡塞武装", "联军"],
        "events_today": 12,
        "last_event": "商船遇袭",
    },
    {
        "id": "sudan",
        "name": "苏丹喀土穆",
        "lat": 15.5, "lon": 32.5,
        "intensity": 80,
        "category": "civil_war",
        "actors": ["SAF", "RSF"],
        "events_today": 22,
        "last_event": "RSF无人机袭击",
    },
    {
        "id": "myanmar",
        "name": "缅甸边境",
        "lat": 21.0, "lon": 96.0,
        "intensity": 65,
        "category": "civil_war",
        "actors": ["军政府", "PDF"],
        "events_today": 15,
        "last_event": "边境哨所交火",
    },
    {
        "id": "sahel",
        "name": "萨赫勒地区",
        "lat": 14.0, "lon": 0.0,
        "intensity": 60,
        "category": "insurgency",
        "actors": ["JNIM", "政府军"],
        "events_today": 9,
        "last_event": "军车遇IED",
    },
    {
        "id": "taiwan-strait",
        "name": "台海",
        "lat": 24.0, "lon": 120.0,
        "intensity": 45,
        "category": "tension",
        "actors": ["PLA", "ROC军"],
        "events_today": 3,
        "last_event": "PLA军机越中线",
    },
    {
        "id": "korean-dmz",
        "name": "朝鲜半岛",
        "lat": 38.3, "lon": 127.0,
        "intensity": 35,
        "category": "tension",
        "actors": ["朝鲜", "韩国/美军"],
        "events_today": 1,
        "last_event": "试射短程导弹",
    },
    {
        "id": "south-china-sea",
        "name": "南海",
        "lat": 12.0, "lon": 115.0,
        "intensity": 50,
        "category": "tension",
        "actors": ["中国海警", "菲越"],
        "events_today": 4,
        "last_event": "海警对峙",
    },
    {
        "id": "syria",
        "name": "叙利亚北部",
        "lat": 36.2, "lon": 37.1,
        "intensity": 70,
        "category": "active_conflict",
        "actors": ["SNA", "SDF", "土耳其"],
        "events_today": 18,
        "last_event": "无人机打击",
    },
]


# 网络战事件（参考 n01d-overwatch）
CYBER_EVENTS = [
    {"target": "美国电力公司", "attacker": "APT29", "type": "ransomware", "severity": 78, "lat": 38.0, "lon": -97.0},
    {"target": "欧盟银行系统", "attacker": "未知", "type": "DDoS", "severity": 62, "lat": 50.0, "lon": 10.0},
    {"target": "台湾半导体", "attacker": "APT41", "type": " espionage", "severity": 85, "lat": 24.5, "lon": 121.0},
    {"target": "乌克兰电网", "attacker": "Sandworm", "type": "wiper", "severity": 90, "lat": 49.0, "lon": 32.0},
    {"target": "印度航空", "attacker": "Patchwork", "type": "phishing", "severity": 55, "lat": 28.6, "lon": 77.2},
]


# 军事调动追踪（参考 OSINT-War-Room）
MILITARY_MOVEMENTS = [
    {"unit": "美国尼米兹航母群", "from": "珍珠港", "to": "西太", "lat": 25.0, "lon": 160.0, "type": "naval"},
    {"unit": "俄罗斯太平洋舰队", "from": "符拉迪沃斯托克", "to": "日本海", "lat": 42.0, "lon": 132.0, "type": "naval"},
    {"unit": "北约快速反应部队", "from": "德国", "to": "波兰", "lat": 52.0, "lon": 19.0, "type": "land"},
    {"unit": "B-52H轰炸机", "from": "英国费尔福德", "to": "波罗的海", "lat": 56.0, "lon": 20.0, "type": "air"},
    {"unit": "中东联军", "from": "沙特", "to": "红海", "lat": 22.0, "lon": 38.0, "type": "naval"},
]


def _tick():
    """每次刷新加点随机波动，让事件流有变化感"""
    for h in CONFLICT_HOTSPOTS:
        h["events_today"] = max(0, h["events_today"] + random.randint(-2, 3))
        h["intensity"] = max(10, min(100, h["intensity"] + random.randint(-3, 3)))
    for c in CYBER_EVENTS:
        c["severity"] = max(20, min(100, c["severity"] + random.randint(-5, 5)))


def get_conflict_snapshot() -> dict:
    _tick()
    return {
        "module": "osint_conflict",
        "hotspots": CONFLICT_HOTSPOTS,
        "cyber_events": CYBER_EVENTS,
        "military_movements": MILITARY_MOVEMENTS,
        "global_threat_level": sum(h["intensity"] for h in CONFLICT_HOTSPOTS) // len(CONFLICT_HOTSPOTS),
        "scanned_at": datetime.now().isoformat(),
    }


# 生成模拟事件流（参考 ACLED 事件数据库风格）
EVENT_TEMPLATES = [
    ("{actor}在{loc}发动炮击", "artillery", 80),
    ("{actor}无人机打击{loc}", "airstrike", 75),
    ("{loc}发生IED爆炸", "ied", 60),
    ("{actor}对{loc}发动网络攻击", "cyber", 55),
    ("{actor}在{loc}集结部队", "mobilization", 40),
    ("{loc}附近的{actor}巡逻队遇袭", "ambush", 65),
    ("{actor}从{loc}撤出部分部队", "withdrawal", 30),
    ("{actor}向{loc}发射导弹", "missile", 85),
    ("{loc}停火协议达成", "ceasefire", 50),
    ("{actor}在{loc}实施空降", "airdrop", 70),
]

LOCATIONS = ["顿巴斯前线", "加沙北部", "红海航道", "苏丹首都", "缅甸若开邦", "萨赫勒", "叙利亚伊德利卜", "南海岛礁"]
ACTORS = ["俄军", "乌军", "IDF", "哈马斯", "胡塞武装", "RSF", "SAF", "PLA", "美军", "北约部队"]


def generate_event_stream(count: int = 20) -> list[dict]:
    """生成事件流"""
    events = []
    now = datetime.now()
    for i in range(count):
        tmpl, etype, base_sev = random.choice(EVENT_TEMPLATES)
        actor = random.choice(ACTORS)
        loc = random.choice(LOCATIONS)
        text = tmpl.format(actor=actor, loc=loc)
        events.append({
            "id": f"ev-{now.strftime('%H%M%S')}-{i}",
            "text": text,
            "type": etype,
            "severity": max(20, min(95, base_sev + random.randint(-10, 10))),
            "time": (now - timedelta(minutes=i * random.randint(5, 30))).isoformat(),
        })
    return events

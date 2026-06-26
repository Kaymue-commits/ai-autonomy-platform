"""
威胁分级分类器 - 参考 worldmonitor _classifier.ts
关键词字典 + 多维度评分 + 5级威胁分级
"""

# ============================================================
# 威胁等级 (THREAT LEVEL)
# ============================================================
THREAT_LEVELS = {
    "critical": {"score": 90, "color": "#ff1744", "label": "CRITICAL", "label_cn": "严重"},
    "high":     {"score": 70, "color": "#ff5722", "label": "HIGH",     "label_cn": "高危"},
    "medium":   {"score": 45, "color": "#ff9800", "label": "MEDIUM",   "label_cn": "中度"},
    "low":      {"score": 25, "color": "#ffc107", "label": "LOW",      "label_cn": "低"},
    "info":     {"score": 0,  "color": "#00e5ff", "label": "INFO",     "label_cn": "信息"},
}


# ============================================================
# 严重事件关键词 (CRITICAL) - 战争/恐袭/核/大规模伤亡
# ============================================================
CRITICAL_KEYWORDS = [
    # 战争
    "war declared", "declaration of war", "act of war", "invasion",
    "military invasion", "full-scale war", "world war",
    # 核
    "nuclear strike", "nuclear attack", "nuclear explosion",
    "atomic bomb", "ICBM launch", "nuclear test",
    "tactical nuke", "radiological",
    # 大规模伤亡
    "mass casualty", "massacre", "genocide", "ethnic cleansing",
    "mass shooting", "terrorism", "terror attack", "terrorist attack",
    # 重要人物遇刺
    "assassination", "assassinated", "coup d'etat", "military coup",
    # 国家级灾难
    "meltdown", "reactor meltdown", "Fukushima", "Chernobyl",
]


# ============================================================
# 高危关键词 (HIGH) - 冲突升级/重大制裁/重大事件
# ============================================================
HIGH_KEYWORDS = [
    # 军事行动
    "airstrike", "air strike", "airstrikes", "missile strike",
    "missile attack", "drone strike", "artillery", "shelling",
    "bombardment", "offensive", "military operation",
    "troop deployment", "mobilization", "naval blockade",
    # 制裁
    "sanctions", "embargo", "trade embargo", "oil embargo",
    "economic sanctions", "swift ban", "asset freeze",
    # 网络战
    "cyberattack", "cyber attack", "cyberwar", "ransomware",
    "critical infrastructure attack", "grid attack",
    "state-sponsored", "APT",
    # 政治
    "regime change", "revolution", "uprising", "insurgency",
    "martial law", "state of emergency",
    # 重大事故
    "oil spill", "pipeline explosion", "refinery fire",
    "blackout", "grid failure",
    # 关键人物
    "president", "prime minister", "defense minister",
    "secretary of state", "supreme leader",
]


# ============================================================
# 中度关键词 (MEDIUM) - 升级迹象/外交/军事调动
# ============================================================
MEDIUM_KEYWORDS = [
    # 外交
    "summit", "treaty", "alliance", "diplomatic", "diplomacy",
    "negotiation", "peace talk", "ceasefire", "armistice",
    "joint statement", "bilateral",
    # 军事
    "military exercise", "war games", "drill", "patrol",
    "carrier group", "fleet", "naval", "air force",
    "base", "deployment", "reinforcement",
    # 贸易
    "tariff", "trade war", "export ban", "export control",
    "decoupling", "supply chain",
    # 国际组织
    "NATO", "UN Security Council", "BRICS", "G7", "G20",
    "OPEC", "OPEC+", "WTO", "IAEA", "WHO",
    # 地缘
    "territorial dispute", "border clash", "skirmish",
    "provocation", "escalation", "tension",
    # 关键设施
    "strait", "chokepoint", "Suez", "Hormuz", "Malacca",
    "Taiwan Strait", "South China Sea",
    # 武器
    "hypersonic", "ballistic", "cruise missile",
    "ICBM", "SAM", "air defense",
]


# ============================================================
# 低等级关键词 (LOW) - 常规新闻
# ============================================================
LOW_KEYWORDS = [
    "election", "vote", "ballot", "parliament", "congress",
    "senate", "policy", "reform", "budget", "spending",
    "protest", "rally", "demonstration",
    "inflation", "interest rate", "fed", "central bank",
    "earnings", "GDP", "employment", "unemployment",
    "merger", "acquisition", "IPO", "funding",
]


# ============================================================
# 多语种关键词 (中文/俄语/阿拉伯语等)
# ============================================================
MULTILINGUAL_KEYWORDS = {
    # 中文
    "战争": 95, "入侵": 92, "核武器": 90, "核打击": 95,
    "导弹袭击": 85, "空袭": 80, "制裁": 70, "禁运": 75,
    "军事演习": 50, "军队调动": 60, "外交": 30, "峰会": 25,
    "谈判": 30, "停火": 50, "贸易战": 60, "关税": 50,
    # 关键国家/地区
    "乌克兰": 60, "俄罗斯": 50, "加沙": 75, "以色列": 55,
    "台湾": 50, "南海": 55, "朝鲜": 50, "伊朗": 50,
    # 事件
    "政变": 90, "革命": 80, "骚乱": 65, "恐怖袭击": 95,
}


# ============================================================
# 主题分类 (TOPIC CLASSIFICATION)
# ============================================================
TOPIC_KEYWORDS = {
    "军事冲突": ["war", "invasion", "airstrike", "missile", "artillery",
                 "shelling", "offensive", "frontline", "battle",
                 "战争", "入侵", "空袭", "导弹", "炮击"],
    "外交": ["diplomatic", "summit", "treaty", "alliance", "negotiation",
              "ceasefire", "peace talk", "外交", "峰会", "条约"],
    "经济": ["economy", "GDP", "inflation", "interest rate", "tariff",
             "trade war", "sanctions", "embargo", "经济", "通胀", "利率"],
    "能源": ["oil", "gas", "energy", "pipeline", "OPEC", "refinery",
             "石油", "天然气", "能源", "管道"],
    "网络": ["cyberattack", "ransomware", "hacking", "data breach",
             "网络攻击", "勒索软件", "黑客"],
    "政治": ["election", "coup", "regime", "parliament", "president",
             "选举", "政变", "议会", "总统"],
    "人道": ["refugee", "humanitarian", "casualty", "massacre",
             "难民", "人道主义", "伤亡"],
    "核武": ["nuclear", "atomic", "ICBM", "uranium", "plutonium",
             "核", "原子弹", "铀"],
    "科技": ["AI", "chip", "semiconductor", "quantum", "5G",
             "人工智能", "芯片", "半导体", "量子"],
}


def classify_topic(text: str) -> str:
    """根据文本判断主题"""
    tl = text.lower()
    best_topic = "其他"
    best_score = 0
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for k in keywords if k.lower() in tl)
        if score > best_score:
            best_score = score
            best_topic = topic
    return best_topic


# ============================================================
# 主分类器
# ============================================================
def classify_threat(text: str) -> dict:
    """
    对文本进行威胁分级评分
    返回: {level, score, matched_keywords, topic}
    """
    text_lower = text.lower()
    score = 0
    matched = []

    # 检查 CRITICAL 关键词
    for kw in CRITICAL_KEYWORDS:
        if kw in text_lower:
            score = max(score, 95)
            matched.append(kw)

    # 检查 HIGH 关键词
    for kw in HIGH_KEYWORDS:
        if kw in text_lower:
            score = max(score, 75)
            matched.append(kw)

    # 检查 MEDIUM 关键词
    for kw in MEDIUM_KEYWORDS:
        if kw in text_lower:
            score = max(score, 50)
            matched.append(kw)

    # 检查 LOW 关键词
    for kw in LOW_KEYWORDS:
        if kw in text_lower:
            if score < 30:
                score = max(score, 25)
            matched.append(kw)

    # 多语种
    for kw, pts in MULTILINGUAL_KEYWORDS.items():
        if kw in text:
            score = max(score, pts)
            matched.append(kw)

    # 确定威胁等级
    if score >= 90:
        level = "critical"
    elif score >= 70:
        level = "high"
    elif score >= 45:
        level = "medium"
    elif score >= 25:
        level = "low"
    else:
        level = "info"

    return {
        "level": level,
        "score": score,
        "matched_keywords": matched[:5],  # 最多返回5个
        "topic": classify_topic(text),
        "label": THREAT_LEVELS[level]["label"],
        "label_cn": THREAT_LEVELS[level]["label_cn"],
        "color": THREAT_LEVELS[level]["color"],
    }


def get_threat_distribution(items: list[dict]) -> dict:
    """统计威胁等级分布"""
    dist = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for item in items:
        level = item.get("severity", "info")
        if level in dist:
            dist[level] += 1
    return dist


if __name__ == "__main__":
    # 测试
    tests = [
        "Russia launches nuclear strike on Ukraine",
        "Fed cuts interest rates by 25 basis points",
        "NATO summit discusses Ukraine alliance",
        "Cyberattack on US power grid causes blackout",
        "OPEC+ agrees to cut oil production",
        "以色列空袭加沙地带 造成重大伤亡",
    ]
    for t in tests:
        r = classify_threat(t)
        print(f"[{r['level']:8s}] score={r['score']:3d} topic={r['topic']:8s} | {t}")
        print(f"          matched: {r['matched_keywords']}")

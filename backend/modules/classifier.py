"""
威胁分级分类器 - 仿 worldmonitor _classifier.ts
基于关键词匹配的新闻事件分类与威胁等级评估

Threat Levels (5级):
  critical - 核打击/入侵/政变/种族灭绝/化学攻击等
  high     - 战争/空袭/导弹/人质/网络攻击/重大灾难
  medium   - 抗议/军事演习/外交危机/经济衰退/基础设施故障
  low      - 选举/条约/气候/经济数据
  info     - 一般新闻

Event Categories (14类):
  conflict / protest / disaster / diplomatic / economic /
  terrorism / cyber / health / environmental / military /
  crime / infrastructure / tech / general
"""
import re
from typing import Optional, Dict, List, Tuple

# ===== 关键词字典 =====
CRITICAL_KEYWORDS = {
    'nuclear strike': 'military',
    'nuclear attack': 'military',
    'nuclear war': 'military',
    'invasion': 'conflict',
    'declaration of war': 'conflict',
    'martial law': 'military',
    'coup': 'military',
    'coup attempt': 'military',
    'genocide': 'conflict',
    'ethnic cleansing': 'conflict',
    'chemical attack': 'terrorism',
    'biological attack': 'terrorism',
    'dirty bomb': 'terrorism',
    'mass casualty': 'conflict',
    'pandemic declared': 'health',
    'health emergency': 'health',
    'nato article 5': 'military',
    'evacuation order': 'disaster',
    'meltdown': 'disaster',
    'nuclear meltdown': 'disaster',
}

HIGH_KEYWORDS = {
    'war': 'conflict',
    'armed conflict': 'conflict',
    'airstrike': 'conflict',
    'air strike': 'conflict',
    'drone strike': 'conflict',
    'missile': 'military',
    'missile launch': 'military',
    'troops deployed': 'military',
    'military escalation': 'military',
    'bombing': 'conflict',
    'casualties': 'conflict',
    'hostage': 'terrorism',
    'terrorist': 'terrorism',
    'terror attack': 'terrorism',
    'assassination': 'crime',
    'cyber attack': 'cyber',
    'ransomware': 'cyber',
    'data breach': 'cyber',
    'sanctions': 'economic',
    'embargo': 'economic',
    'earthquake': 'disaster',
    'tsunami': 'disaster',
    'hurricane': 'disaster',
    'typhoon': 'disaster',
}

MEDIUM_KEYWORDS = {
    'protest': 'protest',
    'protests': 'protest',
    'riot': 'protest',
    'riots': 'protest',
    'unrest': 'protest',
    'demonstration': 'protest',
    'strike action': 'protest',
    'military exercise': 'military',
    'naval exercise': 'military',
    'arms deal': 'military',
    'weapons sale': 'military',
    'diplomatic crisis': 'diplomatic',
    'ambassador recalled': 'diplomatic',
    'expel diplomats': 'diplomatic',
    'trade war': 'economic',
    'tariff': 'economic',
    'recession': 'economic',
    'inflation': 'economic',
    'market crash': 'economic',
    'flood': 'disaster',
    'flooding': 'disaster',
    'wildfire': 'disaster',
    'volcano': 'disaster',
    'eruption': 'disaster',
    'outbreak': 'health',
    'epidemic': 'health',
    'infection spread': 'health',
    'oil spill': 'environmental',
    'pipeline explosion': 'infrastructure',
    'blackout': 'infrastructure',
    'power outage': 'infrastructure',
    'internet outage': 'infrastructure',
    'derailment': 'infrastructure',
}

LOW_KEYWORDS = {
    'election': 'diplomatic',
    'vote': 'diplomatic',
    'referendum': 'diplomatic',
    'summit': 'diplomatic',
    'treaty': 'diplomatic',
    'agreement': 'diplomatic',
    'negotiation': 'diplomatic',
    'talks': 'diplomatic',
    'peacekeeping': 'diplomatic',
    'humanitarian aid': 'diplomatic',
    'ceasefire': 'diplomatic',
    'peace treaty': 'diplomatic',
    'climate change': 'environmental',
    'emissions': 'environmental',
    'pollution': 'environmental',
    'deforestation': 'environmental',
    'drought': 'environmental',
    'vaccine': 'health',
    'vaccination': 'health',
    'disease': 'health',
    'virus': 'health',
    'public health': 'health',
    'covid': 'health',
    'interest rate': 'economic',
    'gdp': 'economic',
    'unemployment': 'economic',
    'regulation': 'economic',
}

# Tech 变体专属关键词
TECH_HIGH_KEYWORDS = {
    'major outage': 'infrastructure',
    'service down': 'infrastructure',
    'global outage': 'infrastructure',
    'zero-day': 'cyber',
    'critical vulnerability': 'cyber',
    'supply chain attack': 'cyber',
    'mass layoff': 'economic',
}

TECH_MEDIUM_KEYWORDS = {
    'outage': 'infrastructure',
    'breach': 'cyber',
    'hack': 'cyber',
    'vulnerability': 'cyber',
    'layoff': 'economic',
    'layoffs': 'economic',
    'antitrust': 'economic',
    'monopoly': 'economic',
    'ban': 'economic',
    'shutdown': 'infrastructure',
}

TECH_LOW_KEYWORDS = {
    'ipo': 'economic',
    'funding': 'economic',
    'acquisition': 'economic',
    'merger': 'economic',
    'launch': 'tech',
    'release': 'tech',
    'update': 'tech',
    'partnership': 'economic',
    'startup': 'tech',
    'ai model': 'tech',
    'open source': 'tech',
}

# Finance 变体专属关键词
FINANCE_HIGH_KEYWORDS = {
    'market crash': 'economic',
    'flash crash': 'economic',
    'circuit breaker': 'economic',
    'bank run': 'economic',
    'bank failure': 'economic',
    'currency crisis': 'economic',
    'hyperinflation': 'economic',
    'default': 'economic',
    'sovereign default': 'economic',
}

FINANCE_MEDIUM_KEYWORDS = {
    'volatility': 'economic',
    'sell-off': 'economic',
    'selloff': 'economic',
    'rally': 'economic',
    'bull market': 'economic',
    'bear market': 'economic',
    'correction': 'economic',
    'rate hike': 'economic',
    'rate cut': 'economic',
    'quantitative easing': 'economic',
    'qt': 'economic',
}

# 排除词 (这些词出现时降级为info)
EXCLUSIONS = [
    'protein', 'couples', 'relationship', 'dating', 'diet', 'fitness',
    'recipe', 'cooking', 'shopping', 'fashion', 'celebrity', 'movie',
    'tv show', 'sports', 'game', 'concert', 'festival', 'wedding',
    'vacation', 'travel tips', 'life hack', 'self-care', 'wellness',
]

# 短关键词 (需要 word boundary)
SHORT_KEYWORDS = {
    'war', 'coup', 'ban', 'vote', 'riot', 'riots', 'hack', 'talks', 'ipo', 'gdp',
    'virus', 'disease', 'flood',
}

# ===== 工具函数 =====
def _escape(kw: str) -> str:
    """转义正则特殊字符"""
    return re.escape(kw)


_keyword_regex_cache: Dict[str, re.Pattern] = {}

def _get_regex(kw: str) -> re.Pattern:
    """获取关键词的正则模式 (短词加word boundary)"""
    if kw not in _keyword_regex_cache:
        escaped = _escape(kw)
        if kw in SHORT_KEYWORDS:
            pattern = r'\b' + escaped + r'\b'
        else:
            pattern = escaped  # 长词/短语直接子串匹配
        _keyword_regex_cache[kw] = re.compile(pattern, re.IGNORECASE)
    return _keyword_regex_cache[kw]


def _match_keywords(text_lower: str, keywords: Dict[str, str]) -> Optional[Tuple[str, str]]:
    """在text中找第一个匹配的keyword+category"""
    for kw, cat in keywords.items():
        if _get_regex(kw).search(text_lower):
            return kw, cat
    return None


# ===== 主分类函数 =====
def classify(title: str, variant: Optional[str] = None) -> Dict:
    """
    分类一条新闻标题
    
    Args:
        title: 新闻标题
        variant: 'full' / 'tech' / 'finance' / 'happy' / 'intel'
    
    Returns:
        {
            "level": "critical"|"high"|"medium"|"low"|"info",
            "category": "conflict"|"protest"|...|"general",
            "confidence": 0.0-1.0,
            "keyword": "matched keyword" or None,
            "source": "keyword"
        }
    """
    if not title:
        return {"level": "info", "category": "general", "confidence": 0.3, "keyword": None, "source": "keyword"}
    
    lower = title.lower()
    
    # 排除词
    for ex in EXCLUSIONS:
        if ex in lower:
            return {"level": "info", "category": "general", "confidence": 0.3, "keyword": ex, "source": "keyword"}
    
    is_tech = variant == 'tech'
    is_finance = variant == 'finance'
    
    # Critical
    m = _match_keywords(lower, CRITICAL_KEYWORDS)
    if m:
        return {"level": "critical", "category": m[1], "confidence": 0.9, "keyword": m[0], "source": "keyword"}
    
    # High
    m = _match_keywords(lower, HIGH_KEYWORDS)
    if m:
        return {"level": "high", "category": m[1], "confidence": 0.8, "keyword": m[0], "source": "keyword"}
    
    # Tech 高
    if is_tech:
        m = _match_keywords(lower, TECH_HIGH_KEYWORDS)
        if m:
            return {"level": "high", "category": m[1], "confidence": 0.75, "keyword": m[0], "source": "keyword"}
    
    # Finance 高
    if is_finance:
        m = _match_keywords(lower, FINANCE_HIGH_KEYWORDS)
        if m:
            return {"level": "high", "category": m[1], "confidence": 0.75, "keyword": m[0], "source": "keyword"}
    
    # Medium
    m = _match_keywords(lower, MEDIUM_KEYWORDS)
    if m:
        return {"level": "medium", "category": m[1], "confidence": 0.7, "keyword": m[0], "source": "keyword"}
    
    # Tech 中
    if is_tech:
        m = _match_keywords(lower, TECH_MEDIUM_KEYWORDS)
        if m:
            return {"level": "medium", "category": m[1], "confidence": 0.65, "keyword": m[0], "source": "keyword"}
    
    # Finance 中
    if is_finance:
        m = _match_keywords(lower, FINANCE_MEDIUM_KEYWORDS)
        if m:
            return {"level": "medium", "category": m[1], "confidence": 0.65, "keyword": m[0], "source": "keyword"}
    
    # Low
    m = _match_keywords(lower, LOW_KEYWORDS)
    if m:
        return {"level": "low", "category": m[1], "confidence": 0.6, "keyword": m[0], "source": "keyword"}
    
    # Tech 低
    if is_tech:
        m = _match_keywords(lower, TECH_LOW_KEYWORDS)
        if m:
            return {"level": "low", "category": m[1], "confidence": 0.55, "keyword": m[0], "source": "keyword"}
    
    return {"level": "info", "category": "general", "confidence": 0.3, "keyword": None, "source": "keyword"}


def classify_batch(titles: List[str], variant: Optional[str] = None) -> List[Dict]:
    """批量分类"""
    return [classify(t, variant) for t in titles]


# ===== 统计辅助 =====
THREAT_LEVEL_ORDER = ['critical', 'high', 'medium', 'low', 'info']
THREAT_LEVEL_SCORE = {
    'critical': 100,
    'high': 75,
    'medium': 50,
    'low': 25,
    'info': 0,
}

CATEGORY_TO_REGION = {
    'conflict': ['中东', '东欧', '非洲', '南亚'],
    'protest': ['拉美', '欧洲', '亚洲'],
    'disaster': ['环太平洋', '南亚', '东南亚'],
    'diplomatic': ['欧洲', '中东', '亚洲'],
    'economic': ['北美', '欧洲', '亚洲'],
    'terrorism': ['中东', '非洲', '南亚'],
    'cyber': ['全球'],
    'health': ['全球'],
    'environmental': ['全球'],
    'military': ['中东', '东欧', '亚太'],
    'crime': ['拉美', '北美'],
    'infrastructure': ['北美', '欧洲', '亚洲'],
    'tech': ['北美', '亚洲'],
    'general': ['全球'],
}

CATEGORY_ICONS = {
    'conflict': '⚔️',
    'protest': '✊',
    'disaster': '🌋',
    'diplomatic': '🤝',
    'economic': '💰',
    'terrorism': '💣',
    'cyber': '🔓',
    'health': '🏥',
    'environmental': '🌍',
    'military': '🎖️',
    'crime': '🚔',
    'infrastructure': '⚡',
    'tech': '💻',
    'general': '📰',
}


if __name__ == '__main__':
    # 测试
    test_titles = [
        "NATO article 5 invoked after invasion",
        "Heavy flooding in Pakistan affects millions",
        "OpenAI releases GPT-5 with major improvements",
        "Tech giant announces mass layoffs of 10000 workers",
        "Stock market crash wipes $1 trillion in value",
        "Bitcoin surges past $100k for the first time",
        "Recipe of the day: chocolate cake",
        "Major AWS outage affects global services",
        "Earthquake magnitude 7.2 hits Japan",
        "Climate change talks resume at UN",
    ]
    print("=== 分类测试 ===\n")
    for t in test_titles:
        # 自动判断variant
        variant = None
        if any(k in t.lower() for k in ['gpt', 'openai', 'aws', 'tech', 'startup', 'layoff']):
            variant = 'tech'
        elif any(k in t.lower() for k in ['stock', 'bitcoin', 'market', 'crypto']):
            variant = 'finance'
        r = classify(t, variant)
        icon = CATEGORY_ICONS.get(r['category'], '📰')
        print(f"  [{r['level']:8s}] {icon} {r['category']:14s} ({r['confidence']:.2f})")
        print(f"    {t}")
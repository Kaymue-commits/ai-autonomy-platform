"""
超级 AI 助手模块
- 统一 LLM Provider (支持 OpenAI/DeepSeek/Anthropic/Gemini/通义千问/智谱/Kimi 等 15+ 家)
- Function Calling 工具调用
- 工具集: 调用项目内所有数据 API (情报/金融/OSINT/专业源/自由职业/AI新闻/能源/需求)
- 多轮对话 + 上下文记忆
- 智能分析: 赚钱机会挖掘、威胁分析、趋势总结等
- 对话内自动配置 API Key (用户粘贴 key 即可)
"""
import json
import re
import asyncio
from datetime import datetime
from typing import Any
import httpx

from modules.llm import (
    PROVIDERS, chat_completion, get_active, set_active, init_from_config,
    get_api_key, list_providers,
)


# ============================================================
# API Key 自动识别 (从用户消息中提取)
# ============================================================
# 各 provider 的 key 前缀特征
KEY_PATTERNS = {
    "openai":      re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "deepseek":    re.compile(r"sk-[a-f0-9]{32,}"),
    "anthropic":   re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "gemini":      re.compile(r"AIza[A-Za-z0-9_-]{30,}"),
    "zhipu":       re.compile(r"[a-f0-9]{32}\.[a-zA-Z0-9]{16}"),
    "moonshot":    re.compile(r"sk-[A-Za-z0-9]{40,}"),
    "groq":        re.compile(r"gsk_[A-Za-z0-9]{40,}"),
    "mistral":     re.compile(r"[A-Za-z0-9]{32}"),
    "together":    re.compile(r"[a-f0-9]{64}"),
    "openrouter":  re.compile(r"sk-or-v1-[A-Za-z0-9]{40,}"),
    "siliconflow": re.compile(r"sk-[a-zA-Z0-9]{40,}"),
    "minimax":     re.compile(r"sk-cp-[A-Za-z0-9_.-]{20,}"),
}

# provider 中文别名 (用户可能说 "用 deepseek" / "切换到 claude" / "换成 gpt")
PROVIDER_ALIASES = {
    "openai": ["openai", "gpt", "chatgpt", "gpt-4", "gpt4", "o1", "o3"],
    "deepseek": ["deepseek", "深度求索", "deepseek-chat", "r1"],
    "anthropic": ["anthropic", "claude", "克劳德", "sonnet", "opus", "haiku", "claude3", "claude3.5"],
    "gemini": ["gemini", "google", "谷歌", " bard", "gemini2", "gemini1.5"],
    "qwen": ["qwen", "通义", "通义千问", "千问", "aliyun", "阿里云", "dashscope"],
    "zhipu": ["zhipu", "智谱", "glm", "chatglm"],
    "moonshot": ["moonshot", "kimi", "月之暗面"],
    "lingyi": ["lingyi", "零一", "零一万物", "yi-", "yilightning"],
    "baichuan": ["baichuan", "百川"],
    "mistral": ["mistral", "mixtral"],
    "xai": ["xai", "grok", "马斯克"],
    "groq": ["groq"],
    "together": ["together", "togetherai"],
    "openrouter": ["openrouter", "open router"],
    "siliconflow": ["siliconflow", "硅基", "硅基流动"],
    "minimax": ["minimax", "mimo", "小米", "小米mimo", "xiaomi", "xiaomimimo", "mimo-v2"],
}


def detect_provider_from_text(text: str) -> str:
    """从文本中识别用户想用的 provider"""
    tl = text.lower()
    for pid, aliases in PROVIDER_ALIASES.items():
        for alias in aliases:
            if alias in tl:
                return pid
    return ""


def detect_api_key_from_text(text: str) -> tuple:
    """从文本中提取 API Key, 返回 (provider, key)"""
    # 按特征明显的优先匹配
    priority = ["openrouter", "anthropic", "gemini", "groq", "minimax", "openai", "deepseek", "zhipu", "moonshot", "siliconflow", "mistral", "together"]
    for pid in priority:
        pattern = KEY_PATTERNS.get(pid)
        if not pattern:
            continue
        m = pattern.search(text)
        if m:
            return pid, m.group(0)
    # 通用 sk- 前缀 (可能是 openai/deepseek/moonshot 等)
    m = re.search(r"sk-[A-Za-z0-9_-]{20,}", text)
    if m:
        # 根据上下文猜 provider
        provider = detect_provider_from_text(text)
        if provider:
            return provider, m.group(0)
        return "openai", m.group(0)  # 默认当 openai
    return "", ""


def save_api_key(provider: str, api_key: str, model: str = "") -> bool:
    """保存 API Key 到 config.json"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        # 保存到 provider 专用字段 + 通用字段
        key_field = f"{provider}_api_key"
        config[key_field] = api_key
        config["llm_provider"] = provider
        config["llm_api_key"] = api_key
        if model:
            config["llm_model"] = model
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        # 运行时切换
        set_active(provider, model)
        return True
    except Exception as e:
        print(f"保存 API Key 失败: {e}")
        return False


# ============================================================
# 工具集定义 (暴露给 LLM 的 functions)
# ============================================================
TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "query_global_intel", "description": "查询全球情报事件。获取地缘政治新闻、冲突事件、CII国家关键基础设施指数。用于回答关于全球局势、地缘政治、国际事件的问题。", "parameters": {"type": "object", "properties": {"min_score": {"type": "integer", "description": "最低威胁分数阈值(0-100)", "default": 0}}}}},
    {"type": "function", "function": {"name": "query_finance", "description": "查询金融市场数据: 加密货币实时价格、全球股票指数、预测市场合约。用于回答加密货币、股票、金融市场、投资机会的问题。", "parameters": {"type": "object", "properties": {"filter": {"type": "string", "description": "过滤关键词", "default": ""}}}}},
    {"type": "function", "function": {"name": "query_osint", "description": "查询OSINT冲突追踪数据: 全球冲突热点、网络战事件、军事调动、威胁等级。用于回答关于战争、军事冲突、网络攻击、全球安全的问题。", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "query_specialized", "description": "查询专业实时数据: USGS全球地震、NASA野火、OpenSky航班追踪、GDELT事件。用于回答地震、火灾、航班、真实事件的问题。", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "query_freelance_jobs", "description": "查询自由职业机会: 远程工作、AI生成竞标文案、估算预算。用于回答'能赚多少钱''有哪些工作机会''远程项目'等问题。这是挖掘赚钱机会的核心工具。", "parameters": {"type": "object", "properties": {"keyword": {"type": "string", "description": "技能关键词过滤", "default": ""}}}}},
    {"type": "function", "function": {"name": "query_ai_news", "description": "查询AI新闻雷达: 最新AI论文、产品发布、GitHub Trending项目。用于回答关于AI、人工智能、大模型、技术趋势的问题。", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "query_energy", "description": "查询能源监控数据: 全球电网负载、能源结构、微电网实时流、全球水电站/核电站/光伏电站/风电场/天然气管道。用于回答关于能源、电力、可再生能源的问题。", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "query_satellites", "description": "查询太空追踪数据: 全球卫星实时位置(含Starlink/军事/导航/气象/空间站)、轨道参数、Starlink星座统计。用于回答关于卫星、太空、Starlink、空间站、军事卫星的问题。", "parameters": {"type": "object", "properties": {"group": {"type": "string", "description": "指定分类: starlink/military/stations/navigation/weather/geo", "default": ""}}}}},
    {"type": "function", "function": {"name": "query_tech_news", "description": "查询科技情报: 全球实时科技热点新闻(TechCrunch/TheVerge/36氪/HackerNews等)。用于回答关于科技新闻、技术突破、产品发布、科技公司的问题。", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "query_demands", "description": "查询需求雷达: 已抓取的客户需求和商机。", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "query_aggregator", "description": "全量聚合查询: 从149个数据源并发抓取的新闻流。用于综合分析、跨类别汇总。", "parameters": {"type": "object", "properties": {"category": {"type": "string", "description": "指定分类", "default": ""}}}}},
    {"type": "function", "function": {"name": "analyze_earning_opportunities", "description": "综合分析所有赚钱机会: 汇总自由职业工作+客户需求+预测市场, 计算总潜在收入, 按技能分类, 推荐最优策略。当用户问'能赚多少钱''赚钱机会'时优先调用。", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_threat_assessment", "description": "综合威胁评估: 汇总全球情报+OSINT冲突+专业事件, 给出全球安全态势总览。当用户问'全球安全''威胁等级'时调用。", "parameters": {"type": "object", "properties": {}}}},
]


# ============================================================
# 工具执行器
# ============================================================
async def execute_tool(tool_name: str, args: dict, app_state: dict) -> str:
    """执行工具调用, 返回 JSON 字符串结果"""
    try:
        if tool_name == "query_global_intel":
            from modules.intelligence import scan_global_intel
            data = await scan_global_intel()
            min_score = args.get("min_score", 0)
            events = [e for e in data["events"] if e.get("score", 0) >= min_score]
            return json.dumps({
                "events": events[:15],
                "cii_index_top10": dict(sorted(data["cii_index"].items(), key=lambda x: -x[1])[:10]),
                "total_events": len(events),
            }, ensure_ascii=False)

        elif tool_name == "query_finance":
            from modules.finance import scan_finance
            data = await scan_finance()
            filt = (args.get("filter") or "").lower()
            if filt:
                crypto = [c for c in data["crypto"] if filt in c["symbol"].lower() or filt in c.get("name", "").lower()]
                stocks = [s for s in data["stock_indices"] if filt in s["name"].lower() or filt in s["region"]]
                markets = [m for m in data["prediction_markets"] if filt in m["question"].lower() or filt in m["category"].lower()]
            else:
                crypto, stocks, markets = data["crypto"], data["stock_indices"], data["prediction_markets"]
            return json.dumps({
                "crypto": crypto,
                "stock_indices": stocks,
                "prediction_markets": markets,
            }, ensure_ascii=False)

        elif tool_name == "query_osint":
            from modules.osint import get_conflict_snapshot
            data = get_conflict_snapshot()
            return json.dumps({
                "hotspots": data["hotspots"],
                "cyber_events": data["cyber_events"],
                "military_movements": data["military_movements"],
                "global_threat_level": data["global_threat_level"],
            }, ensure_ascii=False)

        elif tool_name == "query_specialized":
            from modules.specialized import scan_all_specialized
            data = await scan_all_specialized()
            return json.dumps({
                "earthquakes": data["earthquakes"][:10],
                "wildfires": data["wildfires"][:10],
                "flights_count": data["total_flights"],
                "gdelt_events": data["gdelt_events"][:10],
            }, ensure_ascii=False)

        elif tool_name == "query_freelance_jobs":
            from modules.freelance import scan_freelance
            data = await scan_freelance()
            keyword = (args.get("keyword") or "").lower()
            jobs = data["jobs"]
            if keyword:
                jobs = [j for j in jobs if keyword in j["title"].lower() or keyword in j.get("recommended_stack", "").lower()]
            return json.dumps({
                "jobs": jobs,
                "total_value_usd": sum(j["estimated_budget_usd"] for j in jobs),
                "count": len(jobs),
            }, ensure_ascii=False)

        elif tool_name == "query_ai_news":
            from modules.ainews import scan_ai_news
            data = await scan_ai_news()
            return json.dumps({
                "news": data["news"][:15],
                "github_trending": data["github_trending"],
                "topic_distribution": data["topic_distribution"],
            }, ensure_ascii=False)

        elif tool_name == "query_energy":
            from modules.energy import get_energy_snapshot
            data = get_energy_snapshot()
            return json.dumps({
                "global_load_gw": data["global_load_gw"],
                "global_capacity_gw": data["global_capacity_gw"],
                "global_load_pct": data["global_load_pct"],
                "energy_mix": data["energy_mix"],
                "grid_regions": data["grid_regions"],
                "microgrid": data["microgrid"],
                "facilities": data.get("facilities", {}),
                "totals": data.get("totals", {}),
            }, ensure_ascii=False)

        elif tool_name == "query_satellites":
            from modules.satellite import get_satellite_snapshot
            data = await get_satellite_snapshot()
            group_filter = args.get("group", "")
            sats = data.get("all_sats", [])
            if group_filter:
                sats = [s for s in sats if s.get("group") == group_filter]
            return json.dumps({
                "total_tracked": data["total_tracked"],
                "group_counts": data["group_counts"],
                "starlink_info": data.get("starlink_info", {}),
                "satellites": sats[:30],
                "count": len(sats),
            }, ensure_ascii=False)

        elif tool_name == "query_tech_news":
            from modules.technews import scan_tech_news
            data = await scan_tech_news()
            return json.dumps({
                "news": data["news"][:20],
                "total_news": data["total_news"],
                "category_distribution": data["category_distribution"],
                "total_sources": data["total_sources"],
            }, ensure_ascii=False)

        elif tool_name == "query_demands":
            demands = app_state.get("demands", [])
            return json.dumps({
                "demands": [{"title": d.title, "category": d.category, "estimated_value_usd": d.estimated_value_usd,
                             "region": d.region, "city": d.city, "score": d.score, "url": d.url}
                            for d in demands[:20]],
                "total_value_usd": sum(d.estimated_value_usd for d in demands),
                "count": len(demands),
            }, ensure_ascii=False)

        elif tool_name == "query_aggregator":
            from modules.aggregator import aggregate_all
            data = await aggregate_all()
            category = args.get("category")
            if category:
                items = data["items_by_category"].get(category, [])
            else:
                items = data["all_items"][:20]
            return json.dumps({
                "items": items,
                "total_items": data["total_items"],
                "threat_distribution": data["threat_distribution"],
            }, ensure_ascii=False)

        elif tool_name == "analyze_earning_opportunities":
            # 综合赚钱分析: freelance + demands + 预测市场
            from modules.freelance import scan_freelance
            from modules.finance import scan_finance
            fl, fin = await asyncio.gather(scan_freelance(), scan_finance())
            demands = app_state.get("demands", [])
            # 汇总
            freelance_total = fl["total_value_usd"]
            demands_total = sum(d.estimated_value_usd for d in demands)
            # 按技能分类
            by_skill = {}
            for j in fl["jobs"]:
                skill = j.get("bid_type", "其他")
                by_skill.setdefault(skill, {"count": 0, "value": 0})
                by_skill[skill]["count"] += 1
                by_skill[skill]["value"] += j["estimated_budget_usd"]
            # 预测市场机会
            pred_opps = [{"question": m["question"], "yes_pct": m["yes_pct"], "volume_usd": m["volume_usd"]}
                         for m in fin["prediction_markets"] if m["yes_pct"] > 50]
            return json.dumps({
                "freelance_jobs": fl["count"] if "count" in fl else len(fl["jobs"]),
                "freelance_total_usd": freelance_total,
                "freelance_top5": fl["jobs"][:5],
                "demands_count": len(demands),
                "demands_total_usd": demands_total,
                "demands_top5": [{"title": d.title, "value": d.estimated_value_usd} for d in demands[:5]],
                "prediction_market_opportunities": pred_opps,
                "grand_total_usd": freelance_total + demands_total,
                "by_skill": by_skill,
                "recommendation": "建议优先跟进高价值需求, 同时投标匹配技能的自由职业项目",
            }, ensure_ascii=False)

        elif tool_name == "get_threat_assessment":
            from modules.intelligence import scan_global_intel
            from modules.osint import get_conflict_snapshot
            from modules.specialized import scan_all_specialized
            intel, osint, spec = await asyncio.gather(
                scan_global_intel(), asyncio.to_thread(get_conflict_snapshot), scan_all_specialized()
            )
            critical_events = [e for e in intel["events"] if e["severity"] in ("critical", "high")]
            return json.dumps({
                "global_threat_level": osint["global_threat_level"],
                "critical_intel_events": critical_events[:10],
                "conflict_hotspots": [h for h in osint["hotspots"] if h["intensity"] >= 70],
                "cyber_attacks": osint["cyber_events"],
                "major_earthquakes": [q for q in spec["earthquakes"] if q["magnitude"] >= 5.0],
                "wildfires": spec["wildfires"][:5],
                "assessment": f"全球威胁等级 {osint['global_threat_level']}/100, "
                             f"{len(critical_events)} 条高危情报, "
                             f"{len([h for h in osint['hotspots'] if h['intensity'] >= 70])} 个活跃冲突热点",
            }, ensure_ascii=False)

        else:
            return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"工具执行失败: {str(e)}"}, ensure_ascii=False)


# ============================================================
# 系统提示词
# ============================================================
SYSTEM_PROMPT = """【核心指令】你是 NEXUS RADAR 全球情报系统的 AI 助手。你必须优先使用提供的工具来获取真实数据，绝对不能凭空编造或凭记忆回答任何涉及数据、新闻、市场、事件的问题。

【工具使用规则】
- 只要用户问题涉及：赚钱、收入、工作机会、财务、市场、股票、加密货币、价格、全球安全、威胁、冲突、地震、火灾、航班、能源、卫星、科技新闻、AI新闻 等，你必须第一时间调用对应工具获取实时数据。
- 用户问"能赚多少钱"/"赚钱机会"/"赚钱方式"/"怎么赚钱" → 调用 analyze_earning_opportunities
- 用户问"全球安全"/"威胁"/"危险"/"战争" → 调用 get_threat_assessment
- 用户问"AI新闻"/"最新AI"/"大模型" → 调用 query_ai_news
- 用户问"卫星"/"太空"/"Starlink" → 调用 query_satellites
- 用户问"科技"/"科技新闻"/"科技情报" → 调用 query_tech_news
- 用户问"能源"/"电力"/"水电站"/"天然气" → 调用 query_energy
- 用户问"金融"/"股票"/"加密货币"/"行情" → 调用 query_finance
- 每次回答都必须至少调用一个相关工具，除非用户只是闲聊或问好。

【回答风格】
- 用中文回答，结构化、有数据支撑
- 关键数字用 **加粗** 突出
- 用 markdown 格式（列表、表格、分段）
- 最后给出"核心结论"或"行动建议"
- 数据全部来自工具返回，绝不编造

当前时间: {time}"""


# ============================================================
# 对话历史管理
# ============================================================
# 每个会话最多保留最近 20 条消息
MAX_HISTORY = 20
sessions: dict[str, list[dict]] = {}


def get_session(session_id: str) -> list[dict]:
    """获取会话历史"""
    if session_id not in sessions:
        sessions[session_id] = []
    return sessions[session_id]


def add_message(session_id: str, role: str, content: str, tool_calls: list = None, tool_call_id: str = None):
    """添加消息到会话历史"""
    msg = {"role": role, "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    if tool_call_id:
        msg["tool_call_id"] = tool_call_id
    hist = get_session(session_id)
    hist.append(msg)
    # 截断历史
    if len(hist) > MAX_HISTORY:
        sessions[session_id] = hist[-MAX_HISTORY:]


# ============================================================
# 主对话循环 (支持多轮工具调用)
# ============================================================
async def chat(user_message: str, session_id: str, config: dict, app_state: dict) -> dict:
    """
    AI 助手对话主入口
    支持多轮 function calling, 最多 5 轮工具调用
    """
    # 每次都从 config 重新同步, 确保响应外部 config 变更 (如手动清空)
    init_from_config(config)
    llm = get_active()
    # ===== 1. 先检查是否是 API Key 配置指令 =====
    provider, key = detect_api_key_from_text(user_message)
    if key:
        # 若 key 已被专用前缀正则识别为某 provider (如 sk-cp- → minimax), 直接信任
        # 仅当 key 走的是通用 fallback (provider='openai' 默认) 时, 才看用户消息里是否提到了具体 provider
        if provider == "openai":
            mentioned_provider = detect_provider_from_text(user_message)
            final_provider = mentioned_provider or provider
        else:
            final_provider = provider
        models = PROVIDERS.get(final_provider, {}).get("models", [])
        default_model = models[0]["id"] if models else ""
        ok = save_api_key(final_provider, key, default_model)
        if ok:
            provider_name = PROVIDERS.get(final_provider, {}).get("name", final_provider)
            return {
                "reply": f"✅ **API Key 配置成功！**\n\n"
                         f"- 服务商: **{provider_name}**\n"
                         f"- 模型: `{default_model}`\n"
                         f"- 状态: 已激活, 现在可以正常对话了\n\n"
                         f"你可以直接问我: \"帮我找出所有能赚到的钱\" 或 \"全球安全态势如何？\"",
                "tools_used": [],
                "session_id": session_id,
                "key_configured": True,
                "provider": final_provider,
                "model": default_model,
            }
        else:
            return {
                "reply": "⚠️ API Key 保存失败, 请检查 config.json 权限。",
                "tools_used": [],
                "session_id": session_id,
            }

    # ===== 2. 检查是否是切换模型指令 =====
    mentioned = detect_provider_from_text(user_message)
    if mentioned and mentioned != llm["provider"] and not key:
        existing_key = get_api_key(mentioned, config)
        if existing_key:
            models = PROVIDERS.get(mentioned, {}).get("models", [])
            default_model = models[0]["id"] if models else ""
            set_active(mentioned, default_model)
            provider_name = PROVIDERS.get(mentioned, {}).get("name", mentioned)
            return {
                "reply": f"✅ 已切换到 **{provider_name}** (模型: `{default_model}`)\n\n现在可以继续对话了。",
                "tools_used": [],
                "session_id": session_id,
                "provider": mentioned,
                "model": default_model,
            }
        else:
            provider_name = PROVIDERS.get(mentioned, {}).get("name", mentioned)
            return {
                "reply": f"⚠️ 还没有配置 **{provider_name}** 的 API Key。\n\n请把你的 {provider_name} API Key 粘贴到这里, 我会自动配置。",
                "tools_used": [],
                "session_id": session_id,
            }

    # ===== 3. 检查 LLM 是否可用 =====
    if not llm["provider"]:
        return {
            "reply": "⚠️ **未配置 AI 模型**\n\n"
                     "请把任意服务商的 API Key 粘贴到对话框, 我会自动识别并配置:\n\n"
                     "**支持的服务商:**\n"
                     "- OpenAI (GPT-4o): `sk-xxx`\n"
                     "- DeepSeek (V3/R1): `sk-xxx`\n"
                     "- Anthropic (Claude 3.5): `sk-ant-xxx`\n"
                     "- Google Gemini: `AIzaXXX`\n"
                     "- 通义千问 / 智谱GLM / Kimi / Grok\n"
                     "- Groq / Mistral / Together / OpenRouter\n\n"
                     "💡 也可以直接说 \"用 deepseek\" / \"切换到 claude\"",
            "tools_used": [],
            "session_id": session_id,
        }

    # ===== 4. 正常对话 =====
    add_message(session_id, "user", user_message)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))},
    ] + get_session(session_id)

    tools_used = []
    max_rounds = 5

    for round_num in range(max_rounds):
        result = await chat_completion(
            messages=messages,
            tools=TOOLS_SCHEMA,
            config=config,
            temperature=0.7,
            max_tokens=2000,
        )

        if result.get("error"):
            return {
                "reply": f"⚠️ LLM 调用失败: {result['error'][:300]}\n\n请检查 API Key 是否正确, 或尝试切换其他服务商。",
                "tools_used": tools_used,
                "session_id": session_id,
            }

        message = result["message"]

        if message.get("tool_calls"):
            messages.append(message)
            add_message(session_id, "assistant", message.get("content") or "", message["tool_calls"])

            for tc in message["tool_calls"]:
                fn_name = tc["function"]["name"]
                fn_args_str = tc["function"].get("args") or tc["function"].get("arguments") or "{}"
                try:
                    fn_args = json.loads(fn_args_str) if isinstance(fn_args_str, str) else fn_args_str
                except Exception:
                    fn_args = {}
                tools_used.append(fn_name)
                tool_result = await execute_tool(fn_name, fn_args, app_state)
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": tool_result})
                add_message(session_id, "tool", tool_result, tool_call_id=tc["id"])
            continue

        reply = message.get("content", "")
        add_message(session_id, "assistant", reply)
        return {
            "reply": reply,
            "tools_used": tools_used,
            "session_id": session_id,
            "provider": llm["provider"],
            "model": llm["model"],
        }

    return {
        "reply": "已达到最大工具调用轮数。基于已获取的数据，以上是我的分析结果。",
        "tools_used": tools_used,
        "session_id": session_id,
    }


# ============================================================
# 会话管理
# ============================================================
def clear_session(session_id: str):
    """清除会话历史"""
    if session_id in sessions:
        del sessions[session_id]


def list_sessions() -> list[str]:
    """列出所有活跃会话"""
    return list(sessions.keys())

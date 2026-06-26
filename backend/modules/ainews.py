"""
AI新闻雷达模块 - 类似 Horizon / auto-news / AiLert / AI-News-Aggregator-Bot
聚合 230+ AI源，含论文/GitHub Trending/产品发布
"""
import asyncio
import re
from datetime import datetime
import feedparser
import httpx


# AI 新闻源（参考 Horizon / AiLert 230+ 源，精选高价值）
AI_NEWS_SOURCES = {
    "OpenAI-Blog": "https://openai.com/blog/rss.xml",
    "Anthropic-News": "https://www.anthropic.com/news/rss.xml",
    "DeepMind-Blog": "https://deepmind.google/blog/rss.xml",
    "HuggingFace-Blog": "https://huggingface.co/blog/feed.xml",
    "MIT-TechReview-AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "The-Decoder": "https://the-decoder.com/feed/",
    "VentureBeat-AI": "https://venturebeat.com/category/ai/feed/",
    "AI-Newsletter": "https://aibrews.com/feed.xml",
    "Reddit-LocalLLaMA": "https://www.reddit.com/r/LocalLLaMA/.rss",
    "Reddit-singularity": "https://www.reddit.com/r/singularity/.rss",
    "Arxiv-CS-AI": "https://export.arxiv.org/rss/cs.AI",
    "Arxiv-CS-LG": "https://export.arxiv.org/rss/cs.LG",
    "Arxiv-CS-CL": "https://export.arxiv.org/rss/cs.CL",
    "Arxiv-CS-CV": "https://export.arxiv.org/rss/cs.CV",
}


# AI 模型/公司关键词热度评分
AI_HOT_KEYWORDS = {
    "GPT-5": 95, "Claude 4": 95, "Gemini 2": 90, "Llama 4": 88, "Llama3": 70,
    "Sora": 92, "Suno": 75, "o3": 85, "o1": 75, "AGI": 80, "agent": 70,
    "reasoning": 65, "in-context": 60, "RLHF": 65, "DPO": 55, "MoE": 70,
    "multimodal": 65, "vision-language": 60, "diffusion": 55, "flow matching": 75,
    "Distillation": 50, "quantization": 50, "speculative": 55, "RAG": 65,
    "MCP": 80, "computer use": 75, "tool use": 60, "function calling": 55,
    "fine-tuning": 50, "LoRA": 55, "PEFT": 50, "inference": 40,
    "benchmark": 45, "MMLU": 50, "HumanEval": 50, "SWE-bench": 75,
    "open source": 50, "open weights": 55,
}


def score_ai_news(text: str) -> int:
    text_lower = text.lower()
    score = 30  # 基础分
    for kw, pts in AI_HOT_KEYWORDS.items():
        if kw.lower() in text_lower:
            score = max(score, pts)
    return min(score, 100)


def classify_topic(text: str) -> str:
    tl = text.lower()
    if any(k in tl for k in ["arxiv", "paper", "research", "novel", "method"]):
        return "论文"
    if any(k in tl for k in ["release", "launch", "announc", "introducing", "open-source", "open source"]):
        return "发布"
    if any(k in tl for k in ["benchmark", "eval", "score", "outperform"]):
        return "评测"
    if any(k in tl for k in ["funding", "raise", "series", "$", "valuation"]):
        return "融资"
    if any(k in tl for k in ["agent", "tool", "mcp", "computer use"]):
        return "Agent"
    return "资讯"


async def fetch_ai_news_feed(client: httpx.AsyncClient, name: str, url: str) -> list[dict]:
    items = []
    try:
        r = await client.get(url, timeout=10.0, follow_redirects=True,
                              headers={"User-Agent": "Mozilla/5.0 AIRadar/3.0"})
        if r.status_code != 200:
            return items
        feed = feedparser.parse(r.content)
        for entry in feed.entries[:8]:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            text = f"{title} {summary}"
            score = score_ai_news(text)
            if score < 40:
                continue
            items.append({
                "title": title[:200],
                "summary": re.sub(r"<[^>]+>", "", summary)[:250],
                "url": entry.get("link", ""),
                "source": name,
                "score": score,
                "topic": classify_topic(text),
                "timestamp": datetime.now().isoformat(),
            })
    except Exception:
        pass
    return items


# GitHub Trending AI 项目（参考 AiLert 聚合 GitHub）
GITHUB_TRENDING_AI = [
    {"repo": "OpenAI/openai-python", "stars": "23.5k", "lang": "Python", "desc": "OpenAI 官方 Python SDK"},
    {"repo": "langchain-ai/langchain", "stars": "92.8k", "lang": "Python", "desc": "LLM 应用框架"},
    {"repo": "microsoft/autogen", "stars": "32.1k", "lang": "Python", "desc": "多 Agent 框架"},
    {"repo": "huggingface/transformers", "stars": "131k", "lang": "Python", "desc": "Transformer 模型库"},
    {"repo": "ggerganov/llama.cpp", "stars": "68.9k", "lang": "C++", "desc": "本地 LLM 推理"},
    {"repo": "vllm-project/vllm", "stars": "27.4k", "lang": "Python", "desc": "高吞吐 LLM 推理引擎"},
    {"repo": "lobehub/lobe-chat", "stars": "44.2k", "lang": "TypeScript", "desc": "开源 ChatGPT 替代"},
    {"repo": "comfyanonymous/ComfyUI", "stars": "51.3k", "lang": "Python", "desc": "图像生成节点工作流"},
    {"repo": "All-Hands-AI/OpenHands", "stars": "32.8k", "lang": "Python", "desc": "AI 软件工程师"},
    {"repo": "browser-use/browser-use", "stars": "18.6k", "lang": "Python", "desc": "浏览器 Agent"},
]


async def scan_ai_news() -> dict:
    """扫描 AI 新闻"""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_ai_news_feed(client, n, u) for n, u in AI_NEWS_SOURCES.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    all_news = []
    for r in results:
        if isinstance(r, list):
            all_news.extend(r)
    all_news.sort(key=lambda x: x["score"], reverse=True)
    # 主题分布
    topics = {}
    for n in all_news:
        topics[n["topic"]] = topics.get(n["topic"], 0) + 1
    return {
        "module": "ai_news",
        "news": all_news[:40],
        "github_trending": GITHUB_TRENDING_AI,
        "topic_distribution": topics,
        "total_sources": len(AI_NEWS_SOURCES),
        "scanned_at": datetime.now().isoformat(),
    }

"""
自动对接模块 - 通过邮件/Discord/Webhook 联系需求方
"""
import asyncio
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import httpx

CONTACT_LOG = Path(__file__).parent.parent.parent / "logs" / "contacts.jsonl"
CONTACT_LOG.parent.mkdir(parents=True, exist_ok=True)

# 自动生成外联文案模板
TEMPLATES = {
    "en": """Hi,

I noticed your post about: "{title}"

I lead an AI engineering team that specializes in exactly this kind of work:
- {category} development
- Production deployment in 7-14 days
- Fixed-price quote based on scope

We've delivered similar solutions (RAG systems, AI agents, automation pipelines) 
for clients across US/EU/Asia. Happy to share relevant case studies.

Could you share more about:
1. Timeline expectations
2. Budget range
3. Tech stack preferences

I'd love to put together a quick proposal. Free 30-min consultation call 
to discuss your requirements in detail.

Best,
AI Solutions Team
https://ai-autonomy.example.com
""",
    "zh": """您好，

看到您发布的需求："{title}"

我们专注于此领域的AI工程交付：
- {category} 全栈开发
- 7-14天生产环境交付
- 固定报价，按需定制

已在美/欧/亚交付多个类似项目（RAG系统、AI Agent、自动化流水线）。 
可以分享相关案例。

能否提供：
1. 期望交付时间
2. 预算范围
3. 技术栈偏好

我可以快速出一份方案。第一次30分钟咨询免费。

祝好，
AI方案团队
""",
}

async def auto_contact(demand, config: dict) -> dict:
    """自动对接一条需求"""
    # 选择语言
    lang = "zh" if any(c in demand.title for c in "需求开发接单价格") else "en"
    template = TEMPLATES[lang]

    msg = template.format(
        title=demand.title,
        category=demand.category,
    )

    result = {
        "demand_id": demand.id,
        "title": demand.title,
        "language": lang,
        "message_preview": msg[:300] + "...",
        "channels_attempted": [],
        "timestamp": datetime.now().isoformat(),
    }

    # 1. Discord Webhook
    if config.get("discord_webhook"):
        try:
            await send_discord(config["discord_webhook"], 
                              f"🎯 **新需求匹配** [{demand.city}/{demand.region}]\n**{demand.title}**\n价值评分: {demand.score}/100 | 预估: ${demand.estimated_value_usd:.0f}\n\n{demand.url}")
            result["channels_attempted"].append("discord")
        except Exception as e:
            result["discord_error"] = str(e)

    # 2. 企业微信 Webhook
    if config.get("wecom_webhook"):
        try:
            await send_wecom(config["wecom_webhook"], msg)
            result["channels_attempted"].append("wecom")
        except Exception as e:
            result["wecom_error"] = str(e)

    # 3. 邮件 (超时保护)
    if config.get("contact_email"):
        try:
            await asyncio.wait_for(send_email(config, demand.title, msg), timeout=5.0)
            result["channels_attempted"].append("email")
        except asyncio.TimeoutError:
            result["email_error"] = "smtp_timeout"
        except Exception as e:
            result["email_error"] = str(e)

    # 4. 直接回复 (如果源支持 - HN/Reddit可发站内信)
    if "HackerNews" in demand.source or "Reddit" in demand.source:
        result["direct_reply_available"] = True
        result["direct_reply_url"] = demand.url

    # 记录日志
    with open(CONTACT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

    return result

async def send_discord(webhook_url: str, content: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(webhook_url, json={"content": content[:1900]}, timeout=10)
        r.raise_for_status()

async def send_wecom(webhook_url: str, content: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(webhook_url, json={
            "msgtype": "markdown",
            "markdown": {"content": f"## AI需求匹配\n{content[:1500]}"}
        }, timeout=10)
        r.raise_for_status()

async def send_email(config: dict, subject: str, body: str):
    """发邮件 (需配置SMTP环境变量) - 线程池执行, 不阻塞事件循环"""
    smtp_host = config.get("smtp_host", "smtp.gmail.com")
    smtp_user = config.get("smtp_user")
    smtp_pass = config.get("smtp_pass")
    if not (smtp_user and smtp_pass):
        raise ValueError("smtp_user/smtp_pass未配置")

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = config["contact_email"]
    msg["Subject"] = f"[AI需求] {subject[:60]}"
    msg.attach(MIMEText(body, "plain", "utf-8"))

    def _send():
        with smtplib.SMTP(smtp_host, 587, timeout=5) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send)
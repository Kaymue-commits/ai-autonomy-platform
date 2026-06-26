# AI Autonomy Radar · 全球AI需求自动商业化系统

> 🤖 像视频里最左边电脑那样：地球在转，全球AI高价值需求实时涌来 → 自动评分 → 自动对接 → 自动开发 → 钱到你账户

## 📁 项目结构

```
D:\Design\ai-autonomy-platform\
├── backend/
│   ├── main.py                # FastAPI主服务 (SSE实时推送)
│   ├── modules/
│   │   ├── contact.py         # 自动对接 (Discord/微信/邮件)
│   │   ├── builder.py         # 自动开发 (LLM生成代码+方案)
│   │   └── payment.py         # 收款 (Creem国际 + 支付宝/微信国内)
│   └── __init__.py
├── frontend/
│   └── globe.html             # 动态3D地球 + 实时需求面板 (Three.js)
├── workspace/                 # 自动开发的项目落地
├── logs/                      # 对接日志 + 收款记录
├── config.json                # 配置 (API keys / webhook)
├── requirements.txt
├── start.bat                  # Windows一键启动
└── .env.example               # 环境变量模板
```

## 🚀 快速启动

```bat
cd D:\Design\ai-autonomy-platform
start.bat
```

浏览器打开 `http://localhost:7777` → 看到地球在转 + 右侧需求列表在动。

## 🎯 核心功能

### 1. 全球需求雷达
- **抓取源**: Product Hunt / HackerNews Who's Hiring / Reddit / IndieHackers / GitHub Trending / 36氪 / 虎嗅
- **实时**: SSE推送，地球上的点对应真实城市
- **评分**: 0-100分，基于关键词权重（AI Agent 25 / Sora 25 / bounty 30 ...）
- **分类**: 视频生成 / 图像生成 / 语音音乐 / Agent自动化 / 大模型应用 / 计算机视觉 / 数据分析

### 2. 自动对接
- Discord Webhook → 自动推送到你的服务器
- 企业微信机器人 → 国内最常用
- 邮件外联 → 模板化中英文话术
- 触发条件: 评分 ≥ 60 或金额 ≥ $1000

### 3. 自动开发
- 调用 DeepSeek/GPT-4 生成技术方案 (`workspace/<id>/proposal.md`)
- 生成代码骨架 (`workspace/<id>/main.py`)
- 客户验收 → 14天MVP → 30天完整版

### 4. 跨境收款
- **Creem** (国际): 支持 170+ 国家，信用卡/USDC
- **支付宝** (国内): 个人码 / 商户API
- **微信支付** (国内): Native扫码
- 自动路由: 中国客户 → 支付宝，国际客户 → Creem

## 🔑 配置

编辑 `config.json` 或复制 `.env.example` → `.env` 填入:

```json
{
  "creem_api_key": "creem_xxx",        // 注册 https://creem.io
  "alipay_app_id": "2021000123456789",  // 支付宝开放平台
  "deepseek_api_key": "sk-xxx",        // 便宜的中文LLM
  "discord_webhook": "https://discord.com/api/webhooks/xxx",
  "wecom_webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
}
```

**不填也能跑** — 系统会用本地规则匹配 + 默认模板输出，方便先看效果。

## 📡 API

| Endpoint | Method | 说明 |
|---|---|---|
| `/` | GET | 3D地球前端 |
| `/api/demands` | GET | 所有需求列表 |
| `/api/stats` | GET | 统计数据 |
| `/api/stream` | GET | SSE实时推送 |
| `/api/scan` | POST | 手动触发扫描 |
| `/api/contact/{id}` | POST | 自动对接某需求 |
| `/api/build/{id}` | POST | 自动开发某需求 |
| `/api/webhook/creem` | POST | Creem收款回调 |

## 💰 商业模式

需求评分 ≥ 80 → 报价 $5K-$50K  
评分 60-79 → 报价 $1K-$5K  
评分 40-59 → 报价 $200-$1K  
评分 < 40 → 仅监控，不主动联系

## 🛠 技术栈

- 后端: Python 3.11 + FastAPI + SQLAlchemy
- 前端: Three.js + 原生JS (零构建)
- LLM: DeepSeek (主) / GPT-4o-mini (备)
- 部署: 单机即可，10分钟跑通

## 📝 待你提供的信息

启动前请告诉我:
1. **Creem账号** — 去 https://creem.io 注册拿 API key (海外收款必需)
2. **支付宝收款码/商户ID** — 国内收款
3. **微信支付商户号** — 国内收款 (可选)
4. **Discord Webhook** — 实时接收需求推送 (可选，5分钟搞定)
5. **企业微信机器人** — 国内推送 (可选)
6. **DeepSeek API Key** — 自动生成技术方案 (https://platform.deepseek.com, 1块钱能用很久)

不填也能跑，看效果先。

## 🔄 后续升级

- [ ] 加 Twitter/X API 抓KOL发帖
- [ ] 加 LinkedIn Jobs 抓高薪AI岗位
- [ ] 加 Upwork/Freelancer 实时竞标
- [ ] 接 Twilio 自动给客户打电话
- [ ] 接 WhatsApp Business 自动谈单
- [ ] 接 ElevenLabs 自动语音外联 (英语/日语/阿拉伯语)

---

**"地球在转，钱在来"** 🌍💸
# AI Autonomy Radar · 全球AI需求自动商业化系统

> 🤖 像视频里最左边电脑那样：地球在转，全球AI高价值需求实时涌来 → 自动评分 → 自动对接 → 自动开发 → 钱到你账户

![AI Autonomy Radar](./output/screenshot.png)

## 📊 实时状态
- 11个全球信息源自动抓取（Product Hunt / HackerNews / Reddit / GitHub Trending / IndieHackers / 36氪 / 虎嗅等）
- AI需求自动评分（0-100分 + USD价值估算）
- 自动对接（Discord/企业微信/邮件）
- 自动开发（LLM生成技术方案 + 代码骨架）
- 跨境收款（Creem 国际 + 支付宝/微信 国内）

## 🌍 实时3D地球
- Three.js 真实渲染
- NASA Blue Marble 卫星贴图（蓝绿海洋 + 大陆地形 + 山脉凹凸）
- 26 个全球城市真实经纬度定位（北美/欧洲/亚洲/中东/南美/大洋洲）
- 抓取到需求时对应城市自动脉冲扩散 + 中心连线
- 星空背景 + 大气层光晕 Shader
- 鼠标拖拽旋转 / 滚轮缩放

## 🚀 快速启动

### 1. 克隆仓库
```bash
git clone https://github.com/Kaymue-commits/ai-autonomy-platform.git
cd ai-autonomy-platform
```

### 2. 创建虚拟环境并安装依赖
```bash
python -m venv venv
source venv/Scripts/activate    # Windows Git Bash
# 或 venv\Scripts\activate     # Windows CMD
pip install -r requirements.txt
```

### 3. 启动服务
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 7777 --reload
```

或者 Windows 一键启动：
```bat
start.bat
```

### 4. 打开浏览器
```
http://localhost:7777
```

## 📁 项目结构
```
ai-autonomy-platform/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 主服务 (SSE 实时推送)
│   └── modules/
│       ├── contact.py          # 自动对接模块
│       ├── builder.py          # 自动开发模块
│       └── payment.py          # 跨境收款模块
├── frontend/                   # 前端
│   ├── globe.html              # 完整版（真实数据 + SSE）
│   ├── demo.html               # 静态展示版
│   ├── js/
│   │   ├── three.min.js        # Three.js 0.160
│   │   └── OrbitControls.js    # 手写鼠标控制
│   └── textures/
│       ├── earth-blue-marble.jpg    # NASA 真实地球贴图
│       ├── earth-topology.png       # 山脉凹凸
│       └── earth-water.png          # 水面反射
├── workspace/                  # 自动开发的项目落地
├── output/                     # 截图 + 日志
├── logs/                       # 对接日志 + 收款记录
├── config.json                 # 配置
├── requirements.txt
├── start.bat                   # Windows 一键启动
├── VERSION                     # 版本号
├── CHANGELOG.md                # 更新日志
└── .env.example                # 环境变量模板
```

## 🔑 配置

编辑 `config.json` 或创建 `.env`：

```json
{
  "creem_api_key": "",          // https://creem.io (国际收款)
  "alipay_app_id": "",          // 支付宝开放平台 (国内)
  "wechat_mch_id": "",          // 微信支付商户号 (国内)
  "deepseek_api_key": "",       // https://platform.deepseek.com (LLM方案生成)
  "openai_api_key": "",         // 备选 LLM
  "discord_webhook": "",        // Discord 实时推送
  "wecom_webhook": "",          // 企业微信机器人
  "contact_email": ""           // 自动外联邮箱
}
```

**不填也能跑** — 系统会用本地规则匹配 + 默认模板输出，方便先看效果。

## 📡 API 接口

| Endpoint | Method | 说明 |
|---|---|---|
| `/` | GET | 完整版 3D 地球 |
| `/static/demo.html` | GET | 静态展示版 |
| `/api/demands` | GET | 需求列表（支持 `region`、`min_score` 过滤） |
| `/api/stats` | GET | 统计数据 |
| `/api/stream` | GET | SSE 实时推送 |
| `/api/scan` | POST | 手动触发扫描 |
| `/api/contact/{id}` | POST | 自动对接某需求 |
| `/api/build/{id}` | POST | 自动开发某需求 |
| `/api/webhook/creem` | POST | Creem 收款回调 |

## 💰 商业模式

| 评分区间 | 价值估算 | 自动化策略 |
|---|---|---|
| 80-100 | $5K-$50K | 立即对接 + 报价 |
| 60-79 | $1K-$5K | 对接 + 准备方案 |
| 40-59 | $200-$1K | 仅对接 |
| <40 | <$200 | 仅记录 |

## 🛠 技术栈
- Python 3.11 + FastAPI + SQLAlchemy
- Three.js 0.160 + 原生 JS（零构建）
- Feedparser（RSS 抓取）
- httpx（异步 HTTP）
- sse-starlette（实时推送）
- APScheduler（定时任务）

## 📝 版本
当前版本：**v1.0.0**（[CHANGELOG](./CHANGELOG.md)）

## 📜 License
MIT

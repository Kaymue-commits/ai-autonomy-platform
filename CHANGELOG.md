# Changelog

## [1.0.0] - 2026-06-27
### Added
- 全球AI需求雷达后端 (FastAPI + 多源抓取)
- 动态3D地球前端 (Three.js + NASA Blue Marble真实贴图)
- 11个全球信息源 (ProductHunt/HN/Reddit/GitHub Trending等)
- AI需求自动评分系统 (0-100分 + 价值估算USD)
- 自动对接模块 (Discord/企业微信/邮件)
- 自动开发模块 (LLM生成方案 + 代码骨架)
- 跨境收款模块 (Creem + 支付宝 + 微信)
- SSE实时事件流
- 26个城市真实经纬度定位
- 24-26城市脉冲动画系统

### Tech Stack
- Python 3.11 + FastAPI
- Three.js 0.160 (前端)
- Feedparser (RSS抓取)
- aiohttp/httpx (异步HTTP)

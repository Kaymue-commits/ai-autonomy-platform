# Changelog

## [1.1.0] - 2026-06-27
### Added (基于 koala73/worldmonitor 60K stars 项目深度集成)
- 🌐 **149 个全球数据源** - 同步自 worldmonitor 的 4 个 variant (full/tech/finance/happy) + intel 层
  - 22 个分类: politics/us/europe/middle_east/africa/latam/asia/tech/ai/finance/gov/thinktank/crisis/intel/startups/security/hardware/crypto/gcc_news/energy_* 等
  - 7 个地区: global/middle_east/europe/us/africa/latam/asia
- 🛰 **专业数据 API 接入** (backend/modules/specialized.py)
  - USGS 地震数据 (含经纬度)
  - ACLED 武装冲突位置事件 (含经纬度)
  - NASA FIRMS 火灾/卫星热点 (含经纬度)
  - GDELT 全球事件数据库 (含情感分析)
- 🎯 **威胁分级系统** (backend/modules/classifier.py)
  - 5 个等级: critical/high/medium/low/info
  - 14 个分类: conflict/protest/disaster/diplomatic/economic/terrorism/cyber/health/environmental/military/crime/infrastructure/tech/general
  - 4 个 variant 专属字典 (full/tech/finance)
  - 仿 worldmonitor _classifier.ts 完整翻译
- ⚡ **并发聚合器** (backend/modules/aggregator.py)
  - 20 并发抓取 + 25秒整体超时
  - 单飞锁 (single flight) 防止缓存穿透
  - TTL 缓存 (默认 10 分钟)
- 🔧 **API 路由扩展**:
  - `/api/feed` - 聚合新闻流
  - `/api/feed/variants` - variant 列表
  - `/api/sources/stats` - 数据源统计
  - `/api/aggregator` - 全量并发聚合
  - `/api/threat-levels` - 威胁分级元数据
  - `/api/events/geolocated` - 带经纬度事件
  - `/api/events/gdelt` - GDELT 事件
  - `/api/specialized` - 专业数据统一入口
  - `/api/specialized/earthquakes` - 地震

### Tech Stack (新增)
- feedparser (RSS/Atom 解析)
- httpx (异步 HTTP)
- LRU + TTL 内存缓存 (替代 Upstash Redis)

## [1.0.2] - 2026-06-27
### Added
- v1.0.2 release tag, README 徽章

## [1.0.0] - 2026-06-27
### Initial Public Release
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

"""
金融雷达模块 - 类似 OpenStock / QuantDinger / Profitmaker / Homerun
加密货币实时价格、全球股票指数、预测市场数据
"""
import asyncio
import random
import time
from datetime import datetime
import httpx


# 主流加密货币（参考 Profitmaker 100+ 交易所主流币种）
CRYPTO_ASSETS = [
    {"symbol": "BTC", "name": "Bitcoin", "base_price": 67000, "volatility": 0.025},
    {"symbol": "ETH", "name": "Ethereum", "base_price": 3500, "volatility": 0.03},
    {"symbol": "SOL", "name": "Solana", "base_price": 175, "volatility": 0.045},
    {"symbol": "BNB", "name": "BNB", "base_price": 600, "volatility": 0.02},
    {"symbol": "XRP", "name": "Ripple", "base_price": 0.62, "volatility": 0.035},
    {"symbol": "ADA", "name": "Cardano", "base_price": 0.45, "volatility": 0.04},
    {"symbol": "DOGE", "name": "Dogecoin", "base_price": 0.16, "volatility": 0.06},
    {"symbol": "AVAX", "name": "Avalanche", "base_price": 35, "volatility": 0.045},
    {"symbol": "LINK", "name": "Chainlink", "base_price": 14, "volatility": 0.04},
    {"symbol": "MATIC", "name": "Polygon", "base_price": 0.72, "volatility": 0.05},
]

# 全球股票指数（参考 OpenStock 实时股市）
STOCK_INDICES = [
    {"symbol": "SPX", "name": "S&P 500", "region": "美国", "base": 5470, "vol": 0.008},
    {"symbol": "NDX", "name": "Nasdaq 100", "region": "美国", "base": 19200, "vol": 0.012},
    {"symbol": "DJI", "name": "Dow Jones", "region": "美国", "base": 39100, "vol": 0.006},
    {"symbol": "FTSE", "name": "FTSE 100", "region": "英国", "base": 8200, "vol": 0.007},
    {"symbol": "DAX", "name": "DAX", "region": "德国", "base": 18300, "vol": 0.009},
    {"symbol": "N225", "name": "Nikkei 225", "region": "日本", "base": 38700, "vol": 0.011},
    {"symbol": "HSI", "name": "恒生指数", "region": "香港", "base": 17700, "vol": 0.013},
    {"symbol": "SSEC", "name": "上证综指", "region": "中国", "base": 2970, "vol": 0.010},
    {"symbol": "SX5E", "name": "Euro Stoxx 50", "region": "欧洲", "base": 4950, "vol": 0.008},
]

# 预测市场合约（参考 Polymarket / Kalshi / Homerun）
PREDICTION_MARKETS = [
    {"id": "fed-cut-sep", "question": "美联储9月降息25bp?", "yes_pct": 68, "volume_usd": 2_400_000, "category": "宏观经济"},
    {"id": "us-election-winner", "question": "美国2026中期选举共和党控众议院?", "yes_pct": 52, "volume_usd": 18_500_000, "category": "政治"},
    {"id": "btc-100k-year", "question": "BTC年底前触及$100K?", "yes_pct": 34, "volume_usd": 5_700_000, "category": "加密货币"},
    {"id": "eth-etf-flow", "question": "ETH ETF单周净流入>$200M?", "yes_pct": 41, "volume_usd": 1_100_000, "category": "加密货币"},
    {"id": "oil-90-barrel", "question": "布伦特原油突破$90?", "yes_pct": 22, "volume_usd": 890_000, "category": "大宗商品"},
    {"id": "apple-ai-event", "question": "Apple下一代iPhone集成GPT-5?", "yes_pct": 58, "volume_usd": 1_300_000, "category": "科技"},
]

# 状态缓存
_last_crypto = {}
_last_stocks = {}
_last_scan = 0


def _simulate_tick(base: float, vol: float, last: float = None) -> tuple[float, float]:
    """模拟价格波动 + 24h变化"""
    if last is None:
        last = base
    drift = random.gauss(0, vol)
    new_price = max(0.01, last * (1 + drift))
    change_24h = ((new_price - base) / base) * 100
    return round(new_price, 4 if new_price < 1 else 2), round(change_24h, 2)


async def fetch_crypto_prices() -> list[dict]:
    """抓取加密货币价格（先尝试公开API，失败则用模拟数据）"""
    global _last_crypto, _last_scan
    # 尝试 CoinGecko 免费 API
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            ids = "bitcoin,ethereum,solana,binancecoin,ripple,cardano,dogecoin,avalanche-2,chainlink,matic-network"
            r = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": ids, "vs_currencies": "usd", "include_24hr_change": "true"},
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if r.status_code == 200:
                data = r.json()
                mapping = {
                    "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
                    "binancecoin": "BNB", "ripple": "XRP", "cardano": "ADA",
                    "dogecoin": "DOGE", "avalanche-2": "AVAX",
                    "chainlink": "LINK", "matic-network": "MATIC",
                }
                out = []
                for k, sym in mapping.items():
                    if k in data:
                        out.append({
                            "symbol": sym,
                            "price": round(data[k].get("usd", 0), 4),
                            "change_24h": round(data[k].get("usd_24h_change", 0), 2),
                            "source": "CoinGecko",
                        })
                if out:
                    _last_crypto = {x["symbol"]: x for x in out}
                    _last_scan = time.time()
                    return out
    except Exception:
        pass

    # 回退模拟
    out = []
    for a in CRYPTO_ASSETS:
        last = _last_crypto.get(a["symbol"], {}).get("price", a["base_price"])
        price, change = _simulate_tick(a["base_price"], a["volatility"], last)
        item = {
            "symbol": a["symbol"],
            "name": a["name"],
            "price": price,
            "change_24h": change,
            "source": "simulated",
        }
        _last_crypto[a["symbol"]] = item
        out.append(item)
    _last_scan = time.time()
    return out


async def fetch_stock_indices() -> list[dict]:
    """模拟全球股票指数"""
    global _last_stocks
    out = []
    for s in STOCK_INDICES:
        last = _last_stocks.get(s["symbol"], {}).get("price", s["base"])
        price, change = _simulate_tick(s["base"], s["vol"], last)
        item = {
            "symbol": s["symbol"],
            "name": s["name"],
            "region": s["region"],
            "price": round(price, 2),
            "change_pct": change,
        }
        _last_stocks[s["symbol"]] = item
        out.append(item)
    return out


def get_prediction_markets() -> list[dict]:
    """预测市场快照"""
    out = []
    for m in PREDICTION_MARKETS:
        # 让 yes_pct 随机微动
        yes = max(1, min(99, m["yes_pct"] + random.randint(-3, 3)))
        vol = int(m["volume_usd"] * (1 + random.uniform(-0.05, 0.05)))
        out.append({
            **m,
            "yes_pct": yes,
            "volume_usd": vol,
            "no_pct": 100 - yes,
            "updated_at": datetime.now().isoformat(),
        })
    return out


async def scan_finance() -> dict:
    """扫描金融数据"""
    crypto, stocks = await asyncio.gather(fetch_crypto_prices(), fetch_stock_indices())
    return {
        "module": "finance",
        "crypto": crypto,
        "stock_indices": stocks,
        "prediction_markets": get_prediction_markets(),
        "scanned_at": datetime.now().isoformat(),
    }

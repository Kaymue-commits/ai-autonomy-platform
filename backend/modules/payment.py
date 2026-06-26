"""
收款模块 - Creem (国际) + 支付宝 (国内) + 微信支付
支持: 创建订单 / 查询状态 / Webhook回调
"""
import asyncio
import json
import hashlib
import hmac
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import httpx

PAYMENTS_LOG = Path(__file__).parent.parent.parent / "logs" / "payments.jsonl"
PAYMENTS_LOG.parent.mkdir(parents=True, exist_ok=True)

# ===== Creem 收款 (国际支付, 推荐) =====
# https://docs.creem.io
CREEM_API_BASE = "https://api.creem.io/v1"

class CreemGateway:
    """Creem - 全球支付平台, 支持170+国家"""
    def __init__(self, api_key: str, webhook_secret: str = ""):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

    async def create_checkout(self, product_name: str, amount_usd: float,
                              customer_email: str, success_url: str,
                              cancel_url: str, metadata: dict = None) -> dict:
        """创建Creem支付链接"""
        if not self.api_key:
            return {
                "success": False,
                "error": "CREEM_API_KEY未配置",
                "fallback_url": f"https://creem.io/checkout/demo?amount={amount_usd}&product={product_name}"
            }

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{CREEM_API_BASE}/checkouts",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "product": {
                            "name": product_name,
                            "price": amount_usd,
                            "currency": "USD",
                        },
                        "customer": {"email": customer_email},
                        "success_url": success_url,
                        "cancel_url": cancel_url,
                        "metadata": metadata or {},
                    },
                    timeout=30
                )
                if r.status_code in [200, 201]:
                    data = r.json()
                    return {
                        "success": True,
                        "checkout_url": data.get("checkout_url") or data.get("url"),
                        "session_id": data.get("id"),
                        "gateway": "creem",
                    }
                return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """验证Webhook签名"""
        if not self.webhook_secret:
            return True
        expected = hmac.new(
            self.webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


# ===== 支付宝 (国内收款, 大额/对公) =====
# 使用个人支付宝收款码 + 异步通知 (无需API密钥)
ALIPAY_PERSONAL_QR = "your_alipay_personal_qr_url_or_image_path"
ALIPAY_MERCHANT_ID = ""  # 商户号 (可选)

class AlipayGateway:
    """支付宝 - 适合国内客户大额收款"""
    def __init__(self, app_id: str = "", private_key: str = ""):
        self.app_id = app_id
        self.private_key = private_key

    async def create_order(self, out_trade_no: str, total_amount: float,
                           subject: str, customer_email: str = "") -> dict:
        """创建支付宝订单 (电脑网站支付/手机网站支付)"""
        if not self.app_id:
            # 回退方案: 返回个人收款二维码
            return {
                "success": True,
                "method": "personal_qr",
                "trade_no": out_trade_no,
                "amount_cny": total_amount * 7.2,  # USD to CNY
                "qr_url": ALIPAY_PERSONAL_QR,
                "instruction": f"请扫码支付 ¥{total_amount * 7.2:.2f}, 备注订单号: {out_trade_no}",
            }

        try:
            # 实际签名逻辑需要alipay-sdk, 此处给出API调用示例
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://openapi.alipay.com/gateway.do",
                    data={
                        "app_id": self.app_id,
                        "method": "alipay.trade.precreate",
                        "charset": "utf-8",
                        "sign_type": "RSA2",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "version": "1.0",
                        "biz_content": json.dumps({
                            "out_trade_no": out_trade_no,
                            "total_amount": str(total_amount * 7.2),
                            "subject": subject,
                        })
                    },
                    timeout=30
                )
                return {"success": True, "raw": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ===== 微信支付 (国内) =====
class WechatPayGateway:
    def __init__(self, mch_id: str = "", api_key: str = ""):
        self.mch_id = mch_id
        self.api_key = api_key

    async def create_order(self, out_trade_no: str, total_amount: float, subject: str) -> dict:
        """创建微信支付订单 (Native扫码)"""
        if not self.mch_id:
            return {
                "success": True,
                "method": "personal_qr",
                "trade_no": out_trade_no,
                "amount_cny": total_amount * 7.2,
                "instruction": f"请扫码支付 ¥{total_amount * 7.2:.2f}, 备注: {out_trade_no}",
            }
        return {"success": False, "error": "需配置商户号"}


# ===== 统一支付接口 =====
class PaymentRouter:
    """根据客户地区自动选择支付方式"""
    def __init__(self, config: dict):
        self.creem = CreemGateway(config.get("creem_api_key", ""), 
                                   config.get("creem_webhook_secret", ""))
        self.alipay = AlipayGateway(config.get("alipay_app_id", ""), 
                                     config.get("alipay_private_key", ""))
        self.wechat = WechatPayGateway(config.get("wechat_mch_id", ""), 
                                        config.get("wechat_api_key", ""))

    async def create_payment(self, amount_usd: float, product_name: str,
                             customer_email: str, customer_region: str = "global",
                             success_url: str = "https://ai-autonomy.example.com/success",
                             cancel_url: str = "https://ai-autonomy.example.com/cancel") -> dict:
        """创建支付订单, 自动选通道"""
        order_id = f"AI-{uuid.uuid4().hex[:12].upper()}"

        # 中国/亚洲: 支付宝优先
        if customer_region in ["亚洲", "中国"]:
            alipay_result = await self.alipay.create_order(
                out_trade_no=order_id,
                total_amount=amount_usd,
                subject=product_name,
                customer_email=customer_email
            )
            # 同时给Creem链接作为兜底(国际卡)
            creem_result = await self.creem.create_checkout(
                product_name=product_name,
                amount_usd=amount_usd,
                customer_email=customer_email,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"order_id": order_id, "region": customer_region}
            )
            return {
                "order_id": order_id,
                "amount_usd": amount_usd,
                "amount_cny": amount_usd * 7.2,
                "primary": alipay_result,
                "alternative": creem_result,
                "recommended": "alipay" if customer_region == "中国" else "creem",
            }

        # 全球: Creem
        creem_result = await self.creem.create_checkout(
            product_name=product_name,
            amount_usd=amount_usd,
            customer_email=customer_email,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"order_id": order_id, "region": customer_region}
        )
        return {
            "order_id": order_id,
            "amount_usd": amount_usd,
            "primary": creem_result,
            "alternative": await self.alipay.create_order(order_id, amount_usd, product_name),
            "recommended": "creem",
        }

    def record_payment(self, payment_data: dict):
        """记录支付日志"""
        with open(PAYMENTS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                **payment_data,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False) + "\n")
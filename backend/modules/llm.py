"""
统一 LLM Provider 抽象层
支持全球主流 AI 模型服务商:
- OpenAI 兼容协议: OpenAI / DeepSeek / 通义千问 / 智谱GLM / Moonshot Kimi / 零一万物 / 百川 / Groq / Together / OpenRouter / xAI Grok / SiliconFlow
- Anthropic 协议: Claude 3.5 / Claude 4
- Google Gemini 协议: Gemini 1.5 / 2.0

特性:
- 统一 chat() 接口, 自动适配不同协议
- 支持 function calling (工具调用)
- 运行时切换 provider 和 model
- 自动协议检测
"""
import json
import httpx
from datetime import datetime
from typing import Optional


# ============================================================
# Provider 注册表 (全球主流 AI 服务商)
# ============================================================
# 分为3种协议: openai_compatible / anthropic / gemini
PROVIDERS = {
    # ===== OpenAI 官方 =====
    "openai": {
        "name": "OpenAI",
        "protocol": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "context": 128000, "supports_tools": True},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context": 128000, "supports_tools": True},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": 128000, "supports_tools": True},
            {"id": "o1", "name": "o1", "context": 200000, "supports_tools": False},
            {"id": "o1-mini", "name": "o1-mini", "context": 128000, "supports_tools": False},
            {"id": "o3-mini", "name": "o3-mini", "context": 200000, "supports_tools": True},
        ],
    },
    # ===== DeepSeek =====
    "deepseek": {
        "name": "DeepSeek 深度求索",
        "protocol": "openai_compatible",
        "base_url": "https://api.deepseek.com",
        "models": [
            {"id": "deepseek-chat", "name": "DeepSeek Chat (V3)", "context": 64000, "supports_tools": True},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner (R1)", "context": 64000, "supports_tools": False},
        ],
    },
    # ===== Anthropic Claude =====
    "anthropic": {
        "name": "Anthropic Claude",
        "protocol": "anthropic",
        "base_url": "https://api.anthropic.com",
        "models": [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "context": 200000, "supports_tools": True},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "context": 200000, "supports_tools": True},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context": 200000, "supports_tools": True},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context": 200000, "supports_tools": True},
        ],
    },
    # ===== Google Gemini =====
    "gemini": {
        "name": "Google Gemini",
        "protocol": "gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": [
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "context": 1000000, "supports_tools": True},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "context": 2000000, "supports_tools": True},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "context": 1000000, "supports_tools": True},
        ],
    },
    # ===== 通义千问 (阿里云) =====
    "qwen": {
        "name": "通义千问 Qwen (阿里云)",
        "protocol": "openai_compatible",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": [
            {"id": "qwen-max", "name": "Qwen Max", "context": 32000, "supports_tools": True},
            {"id": "qwen-plus", "name": "Qwen Plus", "context": 128000, "supports_tools": True},
            {"id": "qwen-turbo", "name": "Qwen Turbo", "context": 1000000, "supports_tools": True},
            {"id": "qwen-long", "name": "Qwen Long (1M上下文)", "context": 1000000, "supports_tools": True},
        ],
    },
    # ===== 智谱 GLM =====
    "zhipu": {
        "name": "智谱 GLM",
        "protocol": "openai_compatible",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            {"id": "glm-4-plus", "name": "GLM-4 Plus", "context": 128000, "supports_tools": True},
            {"id": "glm-4", "name": "GLM-4", "context": 128000, "supports_tools": True},
            {"id": "glm-4-flash", "name": "GLM-4 Flash (免费)", "context": 128000, "supports_tools": True},
            {"id": "glm-4-air", "name": "GLM-4 Air", "context": 128000, "supports_tools": True},
        ],
    },
    # ===== Moonshot Kimi =====
    "moonshot": {
        "name": "Moonshot Kimi",
        "protocol": "openai_compatible",
        "base_url": "https://api.moonshot.cn/v1",
        "models": [
            {"id": "moonshot-v1-8k", "name": "Kimi 8K", "context": 8000, "supports_tools": True},
            {"id": "moonshot-v1-32k", "name": "Kimi 32K", "context": 32000, "supports_tools": True},
            {"id": "moonshot-v1-128k", "name": "Kimi 128K", "context": 128000, "supports_tools": True},
        ],
    },
    # ===== 零一万物 Yi =====
    "lingyi": {
        "name": "零一万物 Yi",
        "protocol": "openai_compatible",
        "base_url": "https://api.lingyiwanwu.com/v1",
        "models": [
            {"id": "yi-large", "name": "Yi Large", "context": 32000, "supports_tools": True},
            {"id": "yi-medium", "name": "Yi Medium", "context": 16000, "supports_tools": True},
            {"id": "yi-lightning", "name": "Yi Lightning", "context": 16000, "supports_tools": True},
        ],
    },
    # ===== 百川 Baichuan =====
    "baichuan": {
        "name": "百川 Baichuan",
        "protocol": "openai_compatible",
        "base_url": "https://api.baichuan-ai.com/v1",
        "models": [
            {"id": "Baichuan4-Turbo", "name": "Baichuan4 Turbo", "context": 192000, "supports_tools": True},
            {"id": "Baichuan4-Air", "name": "Baichuan4 Air", "context": 32000, "supports_tools": True},
        ],
    },
    # ===== Mistral =====
    "mistral": {
        "name": "Mistral AI",
        "protocol": "openai_compatible",
        "base_url": "https://api.mistral.ai/v1",
        "models": [
            {"id": "mistral-large-latest", "name": "Mistral Large", "context": 128000, "supports_tools": True},
            {"id": "mistral-small-latest", "name": "Mistral Small", "context": 32000, "supports_tools": True},
            {"id": "open-mixtral-8x7b", "name": "Mixtral 8x7B", "context": 32000, "supports_tools": True},
        ],
    },
    # ===== xAI Grok =====
    "xai": {
        "name": "xAI Grok",
        "protocol": "openai_compatible",
        "base_url": "https://api.x.ai/v1",
        "models": [
            {"id": "grok-beta", "name": "Grok Beta", "context": 131072, "supports_tools": True},
            {"id": "grok-vision-beta", "name": "Grok Vision", "context": 8192, "supports_tools": False},
        ],
    },
    # ===== Groq (超快推理) =====
    "groq": {
        "name": "Groq (超快推理)",
        "protocol": "openai_compatible",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "context": 128000, "supports_tools": True},
            {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B", "context": 128000, "supports_tools": True},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "context": 32768, "supports_tools": True},
        ],
    },
    # ===== Together AI =====
    "together": {
        "name": "Together AI",
        "protocol": "openai_compatible",
        "base_url": "https://api.together.xyz/v1",
        "models": [
            {"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "name": "Llama 3.3 70B Turbo", "context": 128000, "supports_tools": True},
            {"id": "Qwen/Qwen2.5-72B-Instruct-Turbo", "name": "Qwen 2.5 72B", "context": 32000, "supports_tools": True},
            {"id": "deepseek-ai/DeepSeek-R1", "name": "DeepSeek R1", "context": 128000, "supports_tools": False},
        ],
    },
    # ===== OpenRouter (聚合100+模型) =====
    "openrouter": {
        "name": "OpenRouter (聚合100+模型)",
        "protocol": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            {"id": "openai/gpt-4o", "name": "GPT-4o (via OR)", "context": 128000, "supports_tools": True},
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet (via OR)", "context": 200000, "supports_tools": True},
            {"id": "google/gemini-2.0-flash-001", "name": "Gemini 2.0 (via OR)", "context": 1000000, "supports_tools": True},
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek V3 (via OR)", "context": 64000, "supports_tools": True},
            {"id": "x-ai/grok-2-1212", "name": "Grok 2 (via OR)", "context": 131072, "supports_tools": True},
        ],
    },
    # ===== SiliconFlow (硅基流动) =====
    "siliconflow": {
        "name": "SiliconFlow 硅基流动",
        "protocol": "openai_compatible",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": [
            {"id": "deepseek-ai/DeepSeek-V3", "name": "DeepSeek V3", "context": 64000, "supports_tools": True},
            {"id": "deepseek-ai/DeepSeek-R1", "name": "DeepSeek R1", "context": 64000, "supports_tools": False},
            {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen 2.5 72B", "context": 32000, "supports_tools": True},
        ],
    },
    # ===== MiniMax (Token Plan) =====
    # 官方文档: https://platform.minimaxi.com/docs/token-plan/quickstart
    # Token Plan 订阅 Key 前缀: sk-cp-xxx
    # 协议: OpenAI 兼容 (稳定性更好, 生态更完善)
    # 模型: MiniMax-M3 (原生支持 thinking + 工具调用)
    "minimax": {
        "name": "MiniMax M3 (Token Plan)",
        "protocol": "openai_compatible",
        "base_url": "https://api.minimaxi.com/v1",
        "models": [
            {"id": "MiniMax-M3", "name": "MiniMax M3 (1M上下文+多模态)", "context": 1000000, "supports_tools": True},
        ],
    },
}


# ============================================================
# 当前激活的 provider / model (运行时状态)
# ============================================================
_active_provider: str = ""   # 由 config 初始化
_active_model: str = ""


def init_from_config(config: dict):
    """从 config 初始化活跃 provider (每次调用都会重新同步 config → 内存)"""
    global _active_provider, _active_model
    # 优先级: llm_provider+key > 各 provider 专用 key
    new_provider = ""
    new_model = ""
    if config.get("llm_provider") and config.get("llm_api_key"):
        new_provider = config["llm_provider"]
        new_model = config.get("llm_model", "")
    elif config.get("deepseek_api_key"):
        new_provider = "deepseek"
    elif config.get("openai_api_key"):
        new_provider = "openai"
    elif config.get("anthropic_api_key"):
        new_provider = "anthropic"
    elif config.get("gemini_api_key"):
        new_provider = "gemini"

    # 若 config 中没有可用 key, 则清空 active (响应配置被清空的情况)
    if not new_provider:
        _active_provider = ""
        _active_model = ""
        return

    _active_provider = new_provider
    if new_model:
        _active_model = new_model
    else:
        models = PROVIDERS.get(_active_provider, {}).get("models", [])
        _active_model = models[0]["id"] if models else ""


def get_active() -> dict:
    """获取当前活跃 provider 信息"""
    p = PROVIDERS.get(_active_provider, {})
    return {
        "provider": _active_provider,
        "provider_name": p.get("name", ""),
        "model": _active_model,
        "protocol": p.get("protocol", ""),
    }


def set_active(provider: str, model: str):
    """运行时切换 provider / model"""
    global _active_provider, _active_model
    if provider not in PROVIDERS:
        raise ValueError(f"未知 provider: {provider}")
    _active_provider = provider
    if model:
        _active_model = model


def get_api_key(provider: str, config: dict) -> str:
    """获取 provider 的 API Key"""
    # 优先从 provider 专用字段读取
    key_map = {
        "openai": "openai_api_key",
        "deepseek": "deepseek_api_key",
        "anthropic": "anthropic_api_key",
        "gemini": "gemini_api_key",
        "qwen": "qwen_api_key",
        "zhipu": "zhipu_api_key",
        "moonshot": "moonshot_api_key",
        "lingyi": "lingyi_api_key",
        "baichuan": "baichuan_api_key",
        "mistral": "mistral_api_key",
        "xai": "xai_api_key",
        "groq": "groq_api_key",
        "together": "together_api_key",
        "openrouter": "openrouter_api_key",
        "siliconflow": "siliconflow_api_key",
        "minimax": "minimax_api_key",
    }
    # 通用字段优先
    if config.get("llm_api_key") and provider == config.get("llm_provider"):
        return config["llm_api_key"]
    field = key_map.get(provider, f"{provider}_api_key")
    return config.get(field, "")


def list_providers(config: dict) -> list[dict]:
    """列出所有 provider 及其配置状态"""
    result = []
    for pid, p in PROVIDERS.items():
        has_key = bool(get_api_key(pid, config))
        result.append({
            "id": pid,
            "name": p["name"],
            "protocol": p["protocol"],
            "base_url": p["base_url"],
            "models": p["models"],
            "has_api_key": has_key,
            "is_active": pid == _active_provider,
        })
    return result


# ============================================================
# 统一 Chat 接口 (适配3种协议)
# ============================================================
async def chat_completion(
    messages: list[dict],
    tools: list[dict] = None,
    config: dict = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> dict:
    """
    统一 chat completion 接口
    返回: {
        "message": {"role", "content", "tool_calls"?},
        "finish_reason": str,
        "model": str,
        "provider": str,
    }
    """
    active = get_active()
    provider_id = active["provider"]
    model = active["model"]
    protocol = active["protocol"]

    if not provider_id or not model:
        return {
            "error": "未配置 LLM provider, 请在设置中配置 API Key",
        }

    api_key = get_api_key(provider_id, config or {})
    if not api_key:
        return {
            "error": f"未配置 {active['provider_name']} 的 API Key",
        }

    provider = PROVIDERS[provider_id]
    base_url = provider["base_url"]

    # 查当前模型是否支持 tools
    model_info = next((m for m in provider["models"] if m["id"] == model), {})
    supports_tools = model_info.get("supports_tools", True) and tools is not None

    import asyncio as _asyncio
    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                if protocol == "openai_compatible":
                    return await _chat_openai(client, base_url, api_key, model, messages, tools if supports_tools else None, temperature, max_tokens, provider_id)
                elif protocol == "anthropic":
                    return await _chat_anthropic(client, base_url, api_key, model, messages, tools if supports_tools else None, temperature, max_tokens, provider_id)
                elif protocol == "gemini":
                    return await _chat_gemini(client, base_url, api_key, model, messages, tools if supports_tools else None, temperature, max_tokens, provider_id)
                else:
                    return {"error": f"不支持的协议: {protocol}"}
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            last_error = e
            if attempt < 2:
                await _asyncio.sleep(2 ** attempt)
                continue
            return {"error": f"网络连接失败 ({provider_id}): {str(e)} 请检查网络或尝试切换其他服务商"}
        except Exception as e:
            return {"error": f"LLM 调用异常 ({provider_id}): {str(e)}"}


# ============================================================
# OpenAI 兼容协议 (覆盖大多数服务商)
# ============================================================
async def _chat_openai(client, base_url, api_key, model, messages, tools, temperature, max_tokens, provider_id):
    """OpenAI 兼容协议"""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    # OpenRouter 需要额外 header
    if provider_id == "openrouter":
        headers["HTTP-Referer"] = "https://nexus-radar.local"
        headers["X-Title"] = "NEXUS Radar"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    r = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
    if r.status_code != 200:
        # 如果带工具调用失败，尝试不带工具调用（降级）
        if tools and r.status_code in (400, 403, 500):
            try:
                payload_no_tools = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                r2 = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload_no_tools)
                if r2.status_code == 200:
                    data2 = r2.json()
                    choice2 = data2["choices"][0]
                    return {
                        "message": choice2["message"],
                        "finish_reason": choice2.get("finish_reason", ""),
                        "model": data2.get("model", model),
                        "provider": provider_id,
                        "_tools_fallback": True,
                    }
            except Exception:
                pass
        return {"error": f"HTTP {r.status_code}: {r.text[:300]}"}
    data = r.json()
    choice = data["choices"][0]
    msg = choice["message"]
    # 过滤 MiniMax M3 等模型的 <think> 思考标签
    if isinstance(msg.get("content"), str):
        content = msg["content"]
        import re as _re
        content = _re.sub(r'^<think>.*?</think>\s*', '', content, flags=_re.DOTALL)
        msg["content"] = content
    return {
        "message": msg,
        "finish_reason": choice.get("finish_reason", ""),
        "model": data.get("model", model),
        "provider": provider_id,
    }


# ============================================================
# Anthropic Claude 协议
# ============================================================
async def _chat_anthropic(client, base_url, api_key, model, messages, tools, temperature, max_tokens, provider_id):
    """Anthropic Claude 协议"""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    # 分离 system 消息 + 转换 OpenAI 格式到 Anthropic 格式
    system_text = ""
    conv_messages = []
    for m in messages:
        if m["role"] == "system":
            system_text += m["content"] + "\n"
        elif m["role"] == "tool":
            # OpenAI -> Anthropic: role=tool -> role=user, content=tool_result block
            conv_messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": m.get("tool_call_id", ""),
                        "content": m.get("content", ""),
                    }
                ],
            })
        elif m["role"] == "assistant" and m.get("tool_calls"):
            # OpenAI assistant tool_calls -> Anthropic assistant content blocks
            blocks = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for tc in m["tool_calls"]:
                try:
                    inp = json.loads(tc["function"].get("args") or "{}")
                except Exception:
                    inp = {}
                blocks.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "input": inp,
                })
            conv_messages.append({"role": "assistant", "content": blocks})
        else:
            conv_messages.append(m)

    payload = {
        "model": model,
        "messages": conv_messages,
        "system": system_text.strip() or "You are a helpful assistant.",
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    # Anthropic tools 格式不同
    if tools:
        payload["tools"] = [
            {
                "name": t["function"]["name"],
                "description": t["function"]["description"],
                "input_schema": t["function"]["parameters"],
            }
            for t in tools
        ]
        payload["tool_choice"] = {"type": "auto"}

    r = await client.post(f"{base_url}/v1/messages", headers=headers, json=payload)
    if r.status_code != 200:
        # 如果带工具调用失败，尝试不带工具调用（降级）
        if tools and r.status_code in (400, 403, 500):
            try:
                payload_no_tools = {
                    "model": model,
                    "messages": conv_messages,
                    "system": system_text.strip() or "You are a helpful assistant.",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                r2 = await client.post(f"{base_url}/v1/messages", headers=headers, json=payload_no_tools)
                if r2.status_code == 200:
                    data2 = r2.json()
                    content2 = ""
                    for block in data2.get("content", []):
                        if block["type"] == "text":
                            content2 += block["text"]
                    return {
                        "message": {"role": "assistant", "content": content2},
                        "finish_reason": data2.get("stop_reason", ""),
                        "model": data2.get("model", model),
                        "provider": provider_id,
                        "_tools_fallback": True,
                    }
            except Exception:
                pass
        return {"error": f"HTTP {r.status_code}: {r.text[:300]}"}
    data = r.json()

    # 转换为统一格式
    content = ""
    tool_calls = []
    for block in data.get("content", []):
        if block["type"] == "text":
            content += block["text"]
        elif block["type"] == "tool_use":
            tool_calls.append({
                "id": block["id"],
                "type": "function",
                "function": {
                    "name": block["name"],
                    "args": json.dumps(block.get("input", {})),
                }
            })

    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls

    return {
        "message": message,
        "finish_reason": data.get("stop_reason", ""),
        "model": data.get("model", model),
        "provider": provider_id,
    }


# ============================================================
# Google Gemini 协议
# ============================================================
async def _chat_gemini(client, base_url, api_key, model, messages, tools, temperature, max_tokens, provider_id):
    """Google Gemini 协议"""
    # 分离 system 消息
    system_text = ""
    contents = []
    for m in messages:
        role = m["role"]
        if role == "system":
            system_text += m["content"] + "\n"
            continue
        # Gemini role: user / model
        gemini_role = "user" if role in ("user", "tool") else "model"
        content_parts = []
        if m.get("content"):
            content_parts.append({"text": m["content"]})
        # 工具结果
        if role == "tool":
            content_parts = [{"text": m.get("content", "")}]
        if content_parts:
            contents.append({"role": gemini_role, "parts": content_parts})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text.strip()}]}

    # Gemini tools 格式
    if tools:
        payload["tools"] = [{
            "functionDeclarations": [
                {
                    "name": t["function"]["name"],
                    "description": t["function"]["description"],
                    "parameters": t["function"]["parameters"],
                }
                for t in tools
            ]
        }]

    url = f"{base_url}/models/{model}:generateContent?key={api_key}"
    r = await client.post(url, json=payload)
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}: {r.text[:300]}"}
    data = r.json()

    # 转换为统一格式
    candidates = data.get("candidates", [])
    if not candidates:
        return {"error": "Gemini 无响应"}
    parts = candidates[0].get("content", {}).get("parts", [])
    content = ""
    tool_calls = []
    for part in parts:
        if "text" in part:
            content += part["text"]
        elif "functionCall" in part:
            fc = part["functionCall"]
            tool_calls.append({
                "id": f"call_{len(tool_calls)}",
                "type": "function",
                "function": {
                    "name": fc["name"],
                    "args": json.dumps(fc.get("args", {})),
                }
            })

    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls

    return {
        "message": message,
        "finish_reason": candidates[0].get("finishReason", ""),
        "model": model,
        "provider": provider_id,
    }

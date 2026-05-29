"""Local AI proxy for the ecommerce prototype.

This backend keeps API keys out of browser code and exposes two endpoints:
  GET  /api/test             Check dependency and key status
  POST /api/generate-copy    Generate Douyin/ecommerce copy via DeepSeek
  POST /api/generate-image   Generate ecommerce images via Seedream/Ark

Run locally:
  cp .env.example .env   # fill in your API keys
  pip install -r backend/requirements.txt
  python backend/proxy.py
"""
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from dotenv import load_dotenv

    _env_file = Path(__file__).resolve().parent.parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass

try:
    from volcenginesdkarkruntime import Ark
    SDK_INSTALLED = True
except ImportError:
    Ark = None  # type: ignore
    SDK_INSTALLED = False

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:*", "http://127.0.0.1:*", "null"]}})

ARK_MODEL_NAME = os.getenv("ARK_IMAGE_MODEL", "doubao-seedream-4-5-251128")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_URL = os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/v1/chat/completions")


def error_response(message: str, status_code: int = 400, **extra: Any):
    payload = {"success": False, "error": message}
    payload.update(extra)
    return jsonify(payload), status_code


@app.route("/api/test", methods=["GET"])
def test():
    return jsonify({
        "success": True,
        "message": "代理服务器运行正常",
        "image_api": {
            "sdk_installed": SDK_INSTALLED,
            "has_api_key": bool(os.getenv("ARK_API_KEY")),
            "model": ARK_MODEL_NAME,
        },
        "text_api": {
            "has_api_key": bool(os.getenv("DEEPSEEK_API_KEY")),
            "model": DEEPSEEK_MODEL,
            "url": DEEPSEEK_URL,
        },
    })


def build_copy_prompt(product: Dict[str, Any], style: str, duration: str) -> str:
    name = str(product.get("name", "")).strip()
    category = str(product.get("category", "未指定")).strip() or "未指定"
    brand = str(product.get("brand", "未指定")).strip() or "未指定"
    material = str(product.get("material", "未指定")).strip() or "未指定"
    color = str(product.get("color", "未指定")).strip() or "未指定"
    highlights = str(product.get("highlights", "未指定")).strip() or "未指定"
    return f"""
请为以下商品生成 3 个不同版本的抖音电商短视频文案。

商品信息：
- 名称：{name}
- 类目：{category}
- 品牌：{brand}
- 材质：{material}
- 颜色：{color}
- 核心卖点：{highlights}

生成要求：
1. 风格：{style}
2. 时长：{duration}
3. 每个版本都要包含吸引人的开头、商品核心卖点、购买/点击行动号召。
4. 语言要像真实抖音电商口播文案，适合运营直接复制后微调。
5. 只输出 3 个编号版本，格式为：1. xxx 2. xxx 3. xxx。
""".strip()


def call_deepseek(prompt: str) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY 环境变量")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "你是一位专业的抖音电商文案策划师，擅长生成可直接试投放的中文商品文案。"},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek HTTP {exc.code}: {body}") from exc
    except Exception as exc:
        raise RuntimeError(f"DeepSeek请求失败: {exc}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"DeepSeek返回格式异常: {json.dumps(data, ensure_ascii=False)[:500]}") from exc


def split_versions(content: str, style: str, duration: str) -> List[Dict[str, Any]]:
    # Prefer explicit 1./2./3. sections; fall back to non-empty paragraphs.
    parts = re.split(r"(?:^|\n)\s*[123][\.．、]\s*", content)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) < 3:
        parts = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    return [
        {"style": style, "duration": duration, "version": i + 1, "content": text}
        for i, text in enumerate(parts[:3])
    ]


@app.route("/api/generate-copy", methods=["POST"])
def generate_copy():
    data = request.get_json(silent=True) or {}
    product = data.get("product") or {}
    if not isinstance(product, dict):
        return error_response("product字段必须是对象", 400)
    if not str(product.get("name", "")).strip():
        return error_response("商品名称不能为空", 400)

    style = str(data.get("style", "直播带货") or "直播带货")
    duration = str(data.get("duration", "30-60秒") or "30-60秒")
    prompt = build_copy_prompt(product, style, duration)
    try:
        content = call_deepseek(prompt)
        versions = split_versions(content, style, duration)
        if not versions:
            return error_response("DeepSeek返回为空", 500, raw=content)
        return jsonify({"success": True, "data": versions, "raw": content})
    except Exception as exc:
        print(f"文案生成失败: {exc}")
        return error_response(str(exc), 500)


@app.route("/api/generate-image", methods=["POST"])
def generate_image():
    if not SDK_INSTALLED:
        return error_response(
            "SDK未安装",
            500,
            message="请先安装依赖：pip install -r backend/requirements.txt",
        )

    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        return error_response(
            "缺少 ARK_API_KEY 环境变量",
            500,
            message="请先设置环境变量：export ARK_API_KEY='你的密钥'",
        )

    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()
    if not prompt:
        return error_response("prompt不能为空", 400)

    image = data.get("image", [])
    if image is None:
        image = []
    if not isinstance(image, list):
        return error_response("image字段必须是数组", 400)

    size = str(data.get("size", "2K") or "2K")
    allowed_sizes = {"1K", "2K", "4K", "1024x1024", "768x1024", "1024x768"}
    if size not in allowed_sizes:
        size = "2K"

    try:
        print(f"接收到图片生成请求: {json.dumps({'prompt': prompt[:80], 'image_count': len(image), 'size': size}, ensure_ascii=False)}")
        client = Ark(base_url=ARK_BASE_URL, api_key=api_key)  # type: ignore[misc]
        images_response = client.images.generate(
            model=ARK_MODEL_NAME,
            prompt=prompt,
            image=image,
            sequential_image_generation="disabled",
            response_format="url",
            size=size,
            stream=False,
            watermark=False,
        )
        return jsonify({
            "success": True,
            "data": [{"url": item.url} for item in images_response.data],
        })
    except Exception as exc:
        print(f"图片生成失败: {exc}")
        return error_response(str(exc), 500)


if __name__ == "__main__":
    print("=== 电商原型 AI 代理服务器 ===")
    print(f"DeepSeek Key状态: {'已配置' if os.getenv('DEEPSEEK_API_KEY') else '未配置'}")
    print(f"Ark Key状态: {'已配置' if os.getenv('ARK_API_KEY') else '未配置'}")
    print(f"Seedream SDK状态: {'已安装' if SDK_INSTALLED else '未安装'}")
    print("代理服务器运行在: http://localhost:5001")
    print("状态检查接口: http://localhost:5001/api/test")
    app.run(host="0.0.0.0", port=5001, debug=False)

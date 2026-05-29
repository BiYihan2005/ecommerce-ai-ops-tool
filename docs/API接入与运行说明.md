# 电商原型 API 接入与运行说明

> 完整说明见项目根目录 [README.md](../README.md)。

## 当前接入状态

- 文案生成：`frontend/index.html` 调用本地代理 `POST http://localhost:5001/api/generate-copy`，由 `backend/proxy.py` 读取 `DEEPSEEK_API_KEY` 后请求 DeepSeek。前端不保存 API Key。
- 图片生成：`frontend/index.html` 调用 `POST http://localhost:5001/api/generate-image`，由 `backend/proxy.py` 读取 `ARK_API_KEY` 后请求火山 Ark / Seedream。
- 状态检查：访问 `http://localhost:5001/api/test` 查看 `has_api_key` 与 SDK 是否安装。

## 本地运行步骤

```bash
cp .env.example .env
# 编辑 .env 填入密钥

python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/proxy.py
```

然后打开 `frontend/index.html`（或 `python3 -m http.server 8080 --directory frontend`），测试：

1. 抖音文案页：填写商品名称，点击「生成抖音文案」。
2. 图片生成页：填写提示词，点击「生成图片」。
3. 接口状态：浏览器访问 `http://localhost:5001/api/test`。

## 注意事项

1. 两个 API Key 需已开通且有效。
2. 接口失败时，查看 `backend/proxy.py` 终端完整报错。
3. 不要把真实 API Key 提交到公开仓库；若曾误提交，请立即作废并重新生成。

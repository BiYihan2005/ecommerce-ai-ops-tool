# 电商运营工具 — 主图与文案自动生成器

面向抖音/电商运营场景的前后端分离原型：批量管理商品、生成短视频文案、AI 生成商品主图。前端为单页应用，后端 Flask 代理负责调用 DeepSeek 与火山 Ark API，**密钥仅保存在服务端，不暴露给浏览器**。

## 项目背景

电商运营日常需要大量商品主图与短视频口播文案。本项目将「商品录入 → 批量任务 → 文案生成 → 图片生成」整合到一个可交互的原型中，并通过本地代理解决前端直连第三方 AI API 时的密钥泄露与 CORS 问题。适合作为全栈 / 前端 / AI 应用方向的课程作业或求职作品集展示。

## 功能亮点

| 模块 | 说明 |
|------|------|
| **首页仪表盘** | 任务统计、快捷入口、最近任务一览 |
| **批量生成** | Excel/CSV 导入预览、在线录入、状态筛选（待生成/已生成） |
| **商品任务** | 任务列表与进度跟踪 |
| **模板库** | 按风格筛选图文模板 |
| **抖音文案** | 调用 DeepSeek 生成 3 版口播文案；代理不可用时自动降级为本地 Mock |
| **AI 图片** | 调用火山 Seedream 生成电商主图，支持参考图与多种尺寸 |
| **设置页** | 开关类交互与偏好配置 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5、CSS3、原生 JavaScript、Lucide Icons |
| 后端 | Python 3、Flask、Flask-CORS |
| AI 服务 | DeepSeek Chat API（文案）、火山 Ark / Seedream（图片） |
| 依赖管理 | pip、`backend/requirements.txt` |
| 配置 | `.env` + `python-dotenv` |

## 项目结构

```
.
├── frontend/
│   └── index.html          # 前端入口（浏览器直接打开）
├── backend/
│   ├── proxy.py            # Flask AI 代理服务
│   └── requirements.txt    # Python 依赖
├── data/
│   ├── ecommerce_test_products.json
│   └── ecommerce_test_products.csv
├── docs/
│   ├── ecommerce_test_report.md
│   └── API接入与运行说明.md
├── .env.example            # 环境变量模板（复制为 .env 后填写）
├── .gitignore
└── README.md
```

## 快速开始

### 1. 克隆仓库

```bash
git clone <your-repo-url>
cd ecommerce-ai-ops-tool   # 替换为你的仓库目录名
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 与 ARK_API_KEY
```

> 没有 API Key 也可以运行前端并体验 Mock 文案；AI 图片生成需要配置 `ARK_API_KEY` 并启动后端。

### 3. 安装依赖并启动后端

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
python backend/proxy.py
```

后端默认监听 http://localhost:5001 健康检查：

```bash
curl http://localhost:5001/api/test
```

### 4. 打开前端

用浏览器直接打开：

```
frontend/index.html
```

或使用本地静态服务（推荐，避免部分浏览器对 `file://` 的限制）：

```bash
python3 -m http.server 8080 --directory frontend
# 访问 http://localhost:8080
```

### 5. 功能验证清单

1. **批量生成** → 点击「加载测试数据」，确认出现 5 条商品
2. **抖音文案** → 填写商品名 →「生成抖音文案」（无 Key 时应看到 Mock 文案）
3. **AI 图片** → 填写提示词 →「生成图片」（需后端 + `ARK_API_KEY`）
4. **接口状态** → 浏览器访问 `http://localhost:5001/api/test`

## 测试数据说明

项目提供两套一致的示例商品（共 5 条），字段包括商品名称、类目、品牌、材质、颜色、核心卖点、期望状态等：

| 文件 | 用途 |
|------|------|
| `data/ecommerce_test_products.json` | 结构化 JSON，便于脚本或扩展读取 |
| `data/ecommerce_test_products.csv` | 可用于 Excel 批量导入演示 |

前端「加载测试数据」按钮会注入内置 Mock 商品（与上述数据一致），无需额外下载文件即可演示批量流程。

自动化测试报告与修复记录见 [`docs/ecommerce_test_report.md`](docs/ecommerce_test_report.md)（Playwright，21/21 通过）。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/test` | 检查代理状态、Key 是否配置、SDK 是否安装 |
| `POST` | `/api/generate-copy` | 生成抖音文案（Body: `product`, `style`, `duration`） |
| `POST` | `/api/generate-image` | 生成商品图片（Body: `prompt`, `image[]`, `size`） |

## API 安全说明

1. **密钥隔离**：`DEEPSEEK_API_KEY`、`ARK_API_KEY` 仅通过环境变量或 `.env` 由 `backend/proxy.py` 读取，前端 JavaScript 中不包含任何真实密钥。
2. **`.env` 不入库**：`.gitignore` 已忽略 `.env`；仓库仅提供 `.env.example` 占位符。
3. **本地代理**：后端仅用于本地开发/demo，默认绑定 `0.0.0.0:5001`，**请勿将未鉴权的实例直接暴露到公网**。
4. **CORS 限制**：当前允许 `localhost` / `127.0.0.1` 来源，生产环境应收紧 `origins` 并增加鉴权（如 API Token、Rate Limit）。
5. **密钥轮换**：若密钥曾误提交到 Git 历史，请立即在平台作废并重新生成，必要时使用 `git filter-repo` 清理历史。

## 截图

> 运行项目后，可将截图放入 `docs/screenshots/` 并在下方引用。

[首页仪表盘](docs/screenshots/1.png) -->
[批量生成功能](docs/screenshots/2.png) -->
[商品任务进度概览](docs/screenshots/3.png) -->
[模板库](docs/screenshots/4.png) -->
[抖音文案生成](docs/screenshots/5.png) -->
[AI 图片生成](docs/screenshots/6.png) -->
[设置页](docs/screenshots/7.png) -->


## 致谢

- [DeepSeek](https://www.deepseek.com/) — 文案生成
- [火山引擎 Ark](https://www.volcengine.com/product/ark) — Seedream 图片生成
- [Lucide Icons](https://lucide.dev/) — 图标库
- 部分商品图片来源于网络，侵删

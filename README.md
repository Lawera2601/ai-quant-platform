# AI 智能量化投研平台 V1

这是一个面向 A 股投研链路的 V1 基础工程。当前阶段只完成项目初始化、后端健康检查、配置/数据库/ORM 骨架、AKShare 日 K Provider，以及一个最小 Vue 前端壳。

V1 最终链路是：股票搜索 -> AKShare 真实行情 -> MySQL -> FastAPI -> K 线 -> 技术指标 -> 量化评分 -> 简单回测 -> 新闻 -> AI 综合分析 -> Vue 前端展示。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus、ECharts、Axios、Vue Router
- 后端：Python 3.9、FastAPI、Pydantic、SQLAlchemy、Uvicorn
- 数据：AKShare、Pandas、NumPy
- 数据库：MySQL 8
- AI：LLM API、Structured Output

## 项目目录

```text
ai-quant-platform/
├── backend/              # FastAPI 后端
│   └── app/
│       ├── api/v1/
│       ├── core/
│       ├── data/providers/
│       ├── db/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       ├── quant/
│       ├── ai/
│       └── main.py
├── frontend/             # Vue 3 前端
│   └── src/
├── tests/                # 后端测试
├── scripts/              # 本地验证脚本
├── docs/                 # 项目规范文档
├── .env.example
├── .gitignore
└── README.md
```

## Python 环境准备

后端统一使用 Python 3.9。建议在项目根目录创建虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r backend/requirements.txt
```

## Node 环境准备

建议使用 Node.js 18+。

```bash
cd frontend
npm install
```

## MySQL 配置

需要本地或远程 MySQL 8，并创建数据库：

```sql
CREATE DATABASE ai_quant DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

当前工程已建立 SQLAlchemy ORM Model，但还没有引入 Alembic，也没有自动建表脚本。

## .env 配置

复制 `.env.example` 为 `.env`，按本机环境填写：

```env
APP_NAME=AI Quant Research Platform
APP_ENV=development
APP_DEBUG=false
CORS_ORIGINS=http://localhost:5173

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=ai_quant

LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
```

前端如需覆盖 API 地址，可复制 `frontend/.env.example` 为 `frontend/.env`。

## 后端启动

```bash
uvicorn backend.app.main:app --reload
```

健康检查：

```bash
curl http://localhost:8000/api/v1/health
```

期望返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok"
  }
}
```

## 前端启动

```bash
cd frontend
npm run dev
```

默认访问 `http://localhost:5173`。

构建检查：

```bash
npm run build
```

## AKShare 真实数据验证

```bash
python scripts/validate_akshare.py --stock-code 600519
```

该脚本会通过 `AKShareStockProvider` 获取贵州茅台 qfq 日 K 数据。网络不可用、AKShare 不可用或字段变化时，脚本会返回失败原因。

## 当前已完成

- 项目基础目录
- FastAPI 应用入口
- `GET /api/v1/health`
- 统一配置管理，从 `.env` 读取 MySQL 和 LLM 配置
- SQLAlchemy Base、Engine、Session
- `DATABASE_DESIGN.md` 对应的六个 ORM Model
- 基础 Pydantic Schema
- `StockDataProvider` 抽象与 `AKShareStockProvider`
- AKShare 中文字段到内部 `snake_case` 字段转换
- 最小 Vue 3 前端与 health 状态展示

## 当前未完成

- 股票搜索、股票列表、股票详情和 K 线 API
- MySQL 建表、迁移和 Upsert
- 技术指标、量化评分和回测
- 新闻服务
- LLM Client 与 AI 综合分析
- 完整前端投研页面和图表

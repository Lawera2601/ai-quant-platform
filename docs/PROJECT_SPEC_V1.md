# AI 智能量化投研平台 V1 项目规范

> 文档版本：V1.2  
> 项目阶段：基础工程 + MVP 链路  
> 后端 Python：3.9

本文只规定 V1 的目标、边界和协作约束。系统边界见 `docs/SYSTEM_DESIGN.md`，API 字段见 `docs/API_SPEC.md`，数据库表结构见 `docs/DATABASE_DESIGN.md`，开发规则见 `docs/DEVELOPMENT_GUIDELINES.md`。

## 1. V1 目标

V1 最终跑通一条真实、可演示、可继续迭代的 A 股投研链路：

```text
股票搜索 -> AKShare 真实行情 -> MySQL -> FastAPI -> K线
-> 技术指标 -> 量化评分 -> 简单回测 -> 新闻 -> AI综合分析 -> Vue 前端展示
```

第一优先级是链路完整、数据真实、字段一致，不追求复杂策略收益。

## 2. 固定技术栈

前端：

- Vue 3
- TypeScript
- Vite
- Element Plus
- ECharts
- Axios
- Vue Router

后端：

- Python 3.9
- FastAPI
- Pydantic
- SQLAlchemy
- Uvicorn

数据、数据库与 AI：

- AKShare
- Pandas
- NumPy
- MySQL 8
- LLM API + Structured Output

暂不引入 LangChain、LangGraph、Redis、Celery、Kafka、微服务、Kubernetes、复杂 Multi-Agent、强化学习或机器学习选股。

## 3. V1 功能边界

- 仅支持 A 股、日 K，历史行情统一使用 `qfq` 前复权。
- 股票代码始终使用 6 位字符串，例如 `"600519"`。
- 开发阶段以 `600519` 贵州茅台作为真实数据验证对象。
- 指标范围：MA5、MA10、MA20、MA60、MACD、RSI14、BOLL。
- 评分范围 0-100，组成：趋势 40、动量 25、成交量 20、风险 15。
- 回测仅做简单策略，遵守 T 日收盘后产生信号、T+1 开盘执行、禁止未来函数。
- AI 只整合和解释真实模块输出，不计算指标、评分或回测结果。

## 4. 模块边界

- Router：参数校验、调用 Service、返回统一响应。
- Service：业务编排。
- Data Provider：访问 AKShare，并把外部字段转换为内部 `snake_case`。
- DB：SQLAlchemy Model、Engine、Session 与持久化。
- Quant：金融计算，不访问 HTTP、AKShare 或 LLM。
- AI：LLM 调用、Prompt、Structured Output。
- Frontend：展示和交互，不计算金融指标。

## 5. 数据与 API 规范

- Base URL：`/api/v1`
- JSON 字段：`snake_case`
- 日期：`YYYY-MM-DD`
- 时间：ISO 8601
- 百分比：内部使用小数，`0.21` 表示 21%
- 成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

API 名称和字段以 `docs/API_SPEC.md` 为准，不得自行修改。

## 6. 数据库范围

V1 固定六张核心表：

```text
stock_basic
stock_daily
stock_indicator
stock_news
backtest_result
ai_analysis
```

表、字段、类型、索引和约束以 `docs/DATABASE_DESIGN.md` 为准。股票代码不得使用整数类型。

## 7. 当前初始化任务

当前只实现基础工程：

- FastAPI 应用可启动。
- `GET /api/v1/health` 返回统一响应。
- 配置从 `.env` 读取 MySQL 与 LLM 配置。
- 建立 SQLAlchemy 基础配置与六个 ORM Model。
- 建立基础 Pydantic Schema。
- 建立 `StockDataProvider` 抽象与 `AKShareStockProvider`。
- Provider 层完成 AKShare 中文字段到内部 `snake_case` 的转换。
- 用真实 AKShare 尝试获取 `600519` qfq 日 K。
- 初始化 Vue 3 + TypeScript + Vite 前端骨架并能构建。

## 8. 明确不做

本阶段不实现完整量化评分、完整回测、AI Agent、RAG、股票预测、用户系统、实盘交易、美股/港股或大量复杂页面。

## 9. 开发前必须阅读

1. `docs/PROJECT_SPEC_V1.md`
2. `docs/SYSTEM_DESIGN.md`
3. `docs/API_SPEC.md`
4. `docs/DATABASE_DESIGN.md`
5. `docs/DEVELOPMENT_GUIDELINES.md`

现有代码与文档冲突时以文档为准。文档之间出现会影响实现的冲突时，先指出并由团队确认。

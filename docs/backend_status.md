# B 后端进度交接单

> 更新时间：本轮协作结束时
> 用途：让新会话 / 新成员无需依赖历史对话即可接续工作。

## 1. 仓库与分支

- 仓库：`D:\WebProject\ai-quant-platform`（本地克隆）
- 上游（主仓库）：`https://github.com/27ye/ai-quant-platform`
- 你的 fork：`https://github.com/Lawera2601/ai-quant-platform`
- 相关分支：
  - `feature/V1-ai-stock-search`：股票搜索/信息（PR #6，已审核通过，待 27ye 合并）
  - `feature/V1-db-news`：本轮 MySQL 建表/迁移 + 行情 Upsert/查询 + 新闻服务（基于 #6 之上，待 PR #6 合并后可 rebase 到 main）
- 本地 `main` 已同步到 `2070c17`（含 PR #3/#4/#5）

## 2. 你（B 后端）已完成的接口

| 接口 | 实现 | PR | 状态 |
|---|---|---|---|
| `GET /api/v1/stocks/{code}/kline` | K线，≥60行 qfq（`StockService` 保证） | #3 | ✅ 已合 main |
| `GET /api/v1/stocks/{code}/indicators` | 指标序列（包装 C `calculate_indicators`） | #5 | ✅ 已合 main |
| `GET /api/v1/stocks/{code}/score` | 评分（包装 C `calculate_quant_score`） | #5 | ✅ 已合 main |
| `POST /api/v1/backtests` | 回测（包装 C `run_backtest`） | #5 | ✅ 已合 main |
| `GET /api/v1/stocks/search?keyword=` | 股票搜索（`regex=False` 子串匹配，≤50 条） | #6 | 🕒 待 27ye 合并 |
| `GET /api/v1/stocks/{code}` | 股票基本信息 | #6 | 🕒 待 27ye 合并 |
| `GET /api/v1/stocks/{code}/news` | 个股新闻（AKShare `stock_news_em` → 统一新闻结构） | #7 | 🕒 本轮新提交 |

## 3. 关键架构 / 约定

- 分层：`Router -> Service -> Data/Provider -> DB`；B 只包装 C 的量化（`calculate_indicators`/`calculate_quant_score`/`run_backtest`），**不重算**。
- 数据层：`AKShareStockProvider` 唯一调 AKShare；新增 `get_stock_news(stock_code, limit)` 返回统一 `snake_case` 新闻字段（`stock_code/title/summary/source/publish_time/url`）。
- **MySQL**：新增 `backend/app/db/migrations.py`（`apply_migrations(engine)` 幂等建 6 表 + `schema_version` 记录版本）；`scripts/migrate_db.py` 建库并迁移。
- **行情 Upsert/查询**：`backend/app/services/market_data_service.py` —— `MarketDataRepository`（`upsert_stock_basic`/`get_stock_basic`/`upsert_daily`/`list_daily`）按 `(stock_code, trade_date)` Upsert；`MarketDataService` 走「先查 MySQL → 缺失调 Provider → 标准化 → Upsert → 返回」。脚本 `scripts/sync_market_data.py` 演示 `600519` 入库并回读。
- **新闻服务**：`backend/app/services/news_service.py` —— `NewsService.get_news(stock_code, limit=10) -> Sequence[NewsItemContext]`，先查 `stock_news`，为空时拉 AKShare 并 Upsert；实现 D 的 `NewsAnalysisService` Protocol。
- 错误：统一业务码 + `ApiResponse`（`40001`/`40002`/`40003`/`50001`/`50002`/`50003`），见 `docs/API_SPEC.md`。
- 契约：`docs/API_SPEC.md`（新增 4.3 股票新闻）。
- 测试：`pytest tests -q` → **111 passed**（基线 95 + 本轮新增 16）。

## 4. 下一步（B）

1. 等 27ye 合并 **PR #6**（搜索），随后把 `feature/V1-db-news` rebase 到 `main`（只剩 DB+新闻增量），再提 PR #7 合并。
2. 合并后同步：`git fetch upstream` → `git checkout main` → `git merge upstream/main`。
3. 进入 Demo 1.0 全链路联调：A 前端 `VITE_USE_MOCK=false` → 逐接口联调 → 删 mock。B 负责确认接口与契约一致、配合 A/D 排查数据问题；D 接入 `NewsService` 到 AI Context（`AnalysisContextProvider` 已用 `NewsItemContext` 契约）。

## 5. 安全提示（本机）

- GitHub 推送需 **PAT 令牌**（`repo` 权限），用完即撤销；用 `git -c credential.helper= push ...` 或把令牌放 URL（注意令牌只在生成时显示一次，别提交、别写进 config）。
- 本环境访问 GitHub 需走代理（`socks5://127.0.0.1:7892` 为 Clash 端口）；直连会 `Recv failure`。
- 后端环境：`.venv`（Python），`backend/requirements.txt`；前端 `frontend/node_modules`。
- 本机 MySQL 已启用并完成真库验证：`python scripts/migrate_db.py` 建 6 表 + `schema_version`（`0 -> 1`）；`python scripts/sync_market_data.py --stock-code 600519` 同步/回读 **244 行**；新闻服务真库取到并落库 5 条。数据库连接只有本地 `.env`（gitignored，含密码，勿提交）。

## 6. 补充说明

- `docs/COLLABORATION.md`：四人协作规范（分工/文件所有权/冲突处理）。
- 曾因脚本改 `docs/API_SPEC.md` 出现编码乱码，已用 `git checkout` 恢复并改为安全方式编辑；现无乱码。

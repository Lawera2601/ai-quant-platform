# AI 智能量化投研平台 — 多人协作规范

> 版本：V0.1（Demo 1.0 阶段）
> 适用范围：A / B / C / D 四名成员
> 目的：明确分工、文件所有权、冲突处理与协作流程，让第一版 Demo 尽快跑通。

---

## 1. 四名成员分工总览

| 成员 | 方向 | 职责 | 难度 |
|---|---|---|---|
| **A** | 前端开发 🎨 | Vue3 项目、首页、股票搜索/详情页、ECharts（K线/指标）、回测展示、AI 分析页、对接后端 API | ⭐⭐⭐☆☆ |
| **B** | 后端 + 金融数据 ⚙️ | FastAPI、AKShare 数据获取、股票搜索/信息/历史K线、基础新闻、MySQL、API 设计、前后端联调 | ⭐⭐⭐⭐☆ |
| **C** | 量化算法 📈 | Pandas 数据处理、MA/MACD/RSI/Bollinger、简单策略、基础回测、收益率/最大回撤/夏普率 | ⭐⭐⭐⭐☆ |
| **D** | AI Agent + 系统集成 🧠 | LLM 接入、Prompt、股票实体识别、Agent、Tool Calling（行情/量化/回测工具）、生成分析报告 | ⭐⭐⭐⭐⭐ |

---

## 2. 第一版 Demo 目标

**完整跑通一次股票分析即可成功。**

```
用户输入"帮我分析一下贵州茅台"
  → 识别股票 600519
  → B 后端 AKShare 获取 K 线
  → C 量化计算 MA/MACD/RSI + 简单回测（收益率/最大回撤/夏普率）
  → D AI 根据这些数据生成分析
  → A 前端展示结果
```

最终页面至少能看到：股票信息、K 线图、MA/MACD/RSI、简单量化评分、回测结果、AI 分析报告。

---

## 3. 文件所有权矩阵（谁负责哪个文件，减少冲突）

> 原则：**每个人只改自己负责的文件**，公共文件只在必要时动、并提前在群里声明。

### 后端（`backend/`）

| 路径 | 负责人 | 说明 |
|---|---|---|
| `app/data/providers/**` | **B** | AKShare 数据获取，唯一允许调 AKShare 的模块 |
| `app/quant/**` | **C** | 指标、评分、信号、回测、绩效 |
| `app/ai/**` | **D** | LLM、Prompt、Agent、Tool、Structured Output |
| `app/services/stock_service.py` | **B** | 股票/行情服务 |
| `app/services/ai_analysis.py`、`analysis_context.py` | **D** | AI 分析服务 |
| `app/models/stock_*.py` | **B** | 股票/行情/指标/新闻 ORM |
| `app/models/ai_analysis.py` | **D** | AI 分析结果 ORM |
| `app/schemas/stock.py` | **B** | 股票/行情 Schema |
| `app/schemas/ai.py` | **D** | AI 分析 Schema |
| `requirements.txt` | **共享** | 加依赖须在群里说明，避免覆盖他人 |
| `app/core/config.py` | **共享** | B 加数据配置、D 加 LLM 配置，加在各自区块 |

### 公共约定文件

| 路径 | 负责人 | 说明 |
|---|---|---|
| `app/api/v1/router.py` | **共享** | 多人分区块添加路由（见第 4 节） |
| `docs/API_SPEC.md` | **共享** | B 写股票接口、D 写 AI 接口 |
| `app/main.py` | **共享** | 尽量少改 |

### 前端（`frontend/`）

| 路径 | 负责人 |
|---|---|
| `frontend/src/**` | **A** |

---

## 4. 共享文件冲突表 + 处理约定

| 共享文件 | 会碰的人 | 冲突点 | 处理约定 |
|---|---|---|---|
| `app/api/v1/router.py` | B、D（+C 需要时） | B 加 `/stock/*`，D 加 `/ai/*` | **只在自己路由段添加**，别动别人段落；改前先 `git fetch upstream` + `git rebase upstream/main` |
| `docs/API_SPEC.md` | B、D | 各写各的接口文档 | 各自加自己的章节，别删别人的 |
| `app/core/config.py` | B、D | B 加数据配置、D 加 LLM 配置 | 各自在类内对应区块添加，不覆盖字段 |
| `requirements.txt` | B、D（+C 如需） | 各自加依赖 | **新增依赖前在群里声明**，用 pip 兼容范围追加，不删除他人条目 |
| `app/main.py` | 少改 | CORS/路由注册 | 只在有明确需要时改，改前在群里说 |

> **通用法则**：改共享文件前，先 `git fetch upstream` → `git checkout main` → `git merge upstream/main` 同步，再 `git rebase upstream/main` 处理冲突；冲突时**双方段落都保留**，只解决真正重叠处。

---

## 5. 功能依赖关系（谁依赖谁）

```
A(前端) ──> B(后端数据 API) ──> AKShare
        ──> C(指标)          ──> D(Agent 分析)
D(Agent) ──> B(get_stock_data 行情) ── call ──> B 的 /stock/history
        ──> C(get_indicators / run_backtest)
```

推进顺序（地基优先）：
1. **B 先交付**：`/stock/search`、`/stock/history`、`/stock/info` —— A、C、D 三家都基于它。
2. **C 再算**：消费 B 的 K 线 → 指标 → 回测。
3. **D 接入**：Agent 调 B 的行情 + C 的指标/回测 → LLM 生成报告。
4. **A 展示**：对接 B/C/D 的接口结果渲染页面。

### 数据源归属（B 与 C）

- **AKShare 数据获取统一归 B**，B 只提供字段规范、格式统一的 K 线/行情数据。
- **C 不重复实现抓取**，直接消费 B 返回的 K 线（或调用 B 的接口），只做指标计算。
- 这样数据口径统一，D 也只接一套。

---

## 6. Git 分支与协作流程（统一规则）

- **仓库模式**：每人 fork 原仓库，各自在分支上开发，PR 回**原仓库 main**。
- **分支命名**：`feature/<模块>-<功能>`，例如 `feature/backend-kline`。
- **不要在 main 上直接开发**，一律在新分支上做。
- **每次开工前必须同步上游**：
  ```powershell
  git fetch upstream
  git checkout main
  git merge upstream/main
  git checkout <你的分支>
  git rebase main
  ```
- **提交/推送/发 PR**：
  ```powershell
  git add <你负责的路径>
  git commit -m "feat(<模块>): <改动说明>"
  git push origin <你的分支>
  # GitHub 上 Open Pull Request -> 原仓库 main
  ```
- **改共享/公共文件前，先在群里声明**再动手。

---

## 7. API 契约（必须统一，A/D 据此对接）

- **Base URL**：统一 `http://localhost:8000/api/v1`。
- **路径规范**：`/api/v1/<资源>/<动作>`，例如：
  - `GET /api/v1/stocks/search?keyword=茅台`
  - `GET /api/v1/stocks/600519/history?start_date=...&end_date=...`
  - `GET /api/v1/stocks/{stock_code}/kline`
- **统一返回格式**：
  ```json
  { "code": 0, "message": "success", "data": {} }
  ```
- **字段规范**：`snake_case`；日期 `YYYY-MM-DD`；股票代码 6 位字符串；百分比用小数（`0.0125` = 1.25%）。
- **错误码**：`40001` 参数错误、`50001` 数据源错误 等，见 `docs/API_SPEC.md`。

> ⚠️ **注意**：Day 1 任务里写的 `GET /api/stock/history/600519` 是简写，**实际以仓库现有 `docs/API_SPEC.md` 的 `/api/v1` + snake_case 规范为准**，避免 A/D 按错路径对接。全员以 `API_SPEC.md` 为准，如需调整先统一再改。

---

## 8. 每日工作流

1. **开工前**：`git fetch upstream` + 同步 main（见第 6 节）。
2. **开发**：只改自己负责的文件；公共文件改动先声明。
3. **验证**：跑测试 + import 检查（后端 `pytest`；前端 `npm run typecheck` / `npm run build`）。
4. **提交**：清晰 commit message。
5. **PR**：push 到 fork → Open PR 回原仓库 main → 说明改动、是否新增依赖、是否改 API/数据库。
6. **收工**：确认 PR 能被合并、无冲突；若触及共享文件，提醒其他人 rebase。

---

## 9. 每期验收（今晚 Demo 1.0 前）

| 成员 | 验收标准 |
|---|---|
| A | Vue 页面成功运行（`npm run dev`） |
| B | FastAPI + AKShare 成功返回数据（`GET /api/v1/stocks/600519/history` 返回 JSON） |
| C | 成功计算 MA（MA5/MA20）指标 |
| D | LLM API 调用成功 + Agent 框架建立 |

---

## 10. 完成报告模板（每次 PR 附上）

- 修改的文件与实现内容
- 实际执行的命令与结果
- 未执行或失败的验证及原因
- 是否新增依赖
- 是否修改 API / 数据库设计
- 已知问题与下一步建议

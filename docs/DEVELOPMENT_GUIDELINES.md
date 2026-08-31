# AI 智能量化投研平台 V1 开发规范

> 文档版本：V1.2  
> 适用范围：全体开发成员与 AI Coding 工具  
> 后端 Python：3.9

## 1. 开发前检查

开始任务前必须完整阅读：

1. `docs/PROJECT_SPEC_V1.md`
2. `docs/SYSTEM_DESIGN.md`
3. `docs/API_SPEC.md`
4. `docs/DATABASE_DESIGN.md`
5. `docs/DEVELOPMENT_GUIDELINES.md`

文档与代码冲突时以文档为准。文档之间存在会影响实现的冲突时，先指出并由团队确认。

## 2. 固定约束

- 后端统一使用 Python 3.9。
- 不得私自更换 Vue 3、FastAPI、MySQL、SQLAlchemy、AKShare、Pandas 等核心技术栈。
- 不得私自修改 API、数据库结构或模块边界。
- 不实现 V1 范围外能力，不引入复杂 Multi-Agent、RAG、微服务或异步任务基础设施。
- Secret 只能从环境变量读取，仓库只提交 `.env.example`。

## 3. 标准流程

```text
阅读规范和现有代码
-> 明确当前任务边界
-> 搜索可复用实现
-> 最小范围修改
-> 运行针对性测试
-> 运行 import / lint / build 检查
-> 检查 API、数据库和模块兼容性
-> 提交人工 Review
```

不得声称未实际执行的测试已经通过。

## 4. 最小修改原则

- 只修改完成当前需求必要的文件。
- 优先复用现有模块，再考虑扩展或新建。
- 禁止无关重构、批量重命名、随意删除代码和巨型文件。
- 修改公共函数前必须搜索调用方。
- 新增依赖前确认现有依赖无法完成，并在报告中说明。

## 5. 后端分层

```text
Router -> Service -> Data / Quant / AI / DB
```

- Router：参数校验、Service 调用、响应封装。
- Data：唯一允许调用 AKShare 的模块，负责中文字段转换、日期和百分比规范化。
- Quant：指标、评分、信号、回测和绩效指标。
- AI：LLM 调用、Prompt 和 Structured Output。
- DB：SQLAlchemy 模型、会话和持久化。

Router 不得直接调用 AKShare、计算指标、运行回测、调用 LLM 或编写大量 SQL。

## 6. 数据规则

- 股票代码统一为 6 位字符串。
- API 日期为 `YYYY-MM-DD`，内部使用 `date` / `datetime` / Pandas 时间类型。
- 百分比统一使用小数，`0.21` 表示 21%。
- 行情、指标、评分和回测统一使用 qfq 数据。
- 回测遵守 T 日收盘产生信号、T+1 开盘执行，禁止未来函数。
- NaN、空字符串和缺失值必须显式处理。

## 7. 外部服务与异常

AKShare、MySQL 和 LLM 调用必须处理网络错误、超时、空数据、字段变化、限流和服务不可用。

禁止：

```python
try:
    ...
except:
    pass
```

异常边界应记录不含 Secret 的上下文，并转换为清晰错误。

## 8. Mock 与真实性

- 单元测试可以使用明确标记的替身或 monkeypatch。
- 禁止用固定行情、评分、收益率或 AI 文本冒充真实结果。
- 真实数据验证必须实际调用数据源；无法调用时报告原始失败原因。

## 9. 前端规则

- API 请求集中在 `frontend/src/api/`。
- API 类型集中在 `frontend/src/types/`，避免 `any`。
- 前端只负责展示、交互和格式化，不计算金融指标。
- 页面和组件按职责拆分，避免巨型单文件组件。

## 10. 测试要求

基础工程至少验证：

- 后端 import。
- FastAPI 启动与 health API。
- ORM Model 加载与关键约束。
- Provider 字段规范化。
- 真实 `600519` qfq 日 K 获取。
- 前端 TypeScript 检查和 Vite build。

## 11. 完成报告

每次任务说明：

- 修改的文件和实现内容。
- 实际执行的命令与结果。
- 未执行或失败的验证及原因。
- 是否新增依赖。
- 是否修改 API。
- 是否修改数据库设计。
- 已知问题和下一步建议。

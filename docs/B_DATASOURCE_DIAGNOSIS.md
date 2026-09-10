# B 数据源实时失败诊断（给 D）

> 结论：`stock_individual_info_em` 与 `stock_zh_a_hist` 的实时失败是**上游/网络问题**，不是 B 代码问题；
> B 已按契约把两者都映射为 `50001`（未伪装成空数据）。以下为可复现诊断与不含凭据的配置说明。

## 1. 现象（与 D 报告一致）

| 数据源 | 接口 | 结果 |
|---|---|---|
| 股票基础信息 | `ak.stock_individual_info_em` → `push2.eastmoney.com/api/qt/stock/get` | `StockDataProviderError` ← `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` |
| 日线行情 | `ak.stock_zh_a_hist` → `push2his.eastmoney.com` | `StockDataProviderError` ← `SSLError`（偶发 `ProxyError`） |
| 新闻 | `ak.stock_news_em` → `search-api-web.eastmoney.com` | 正常 |
| 交易日历 | `ak.tool_trade_date_hist_sina` → `finance.sina.com.cn` | 正常（网络好时） |

## 2. 复现命令

```powershell
$env:PYTHONIOENCODING='utf-8'
./.venv/Scripts/python.exe -c "from datetime import date,timedelta; from backend.app.data.providers.akshare_provider import AKShareStockProvider as P; p=P(); print(p.get_stock_info('600519'))"
./.venv/Scripts/python.exe -c "from datetime import date,timedelta; from backend.app.data.providers.akshare_provider import AKShareStockProvider as P; p=P(); print(p.get_daily_kline('600519', date.today()-timedelta(days=15), date.today()))"
```

## 3. 根因证据

1. **股票信息 = 上游返回 HTTP 502（HTML）**，akshare 直接 `r.json()` 失败：
   ```
   GET https://push2.eastmoney.com/api/qt/stock/get  ->  HTTP 502
   body: '<html><head><title>502 Bad Gateway</title></head>...'
   ```
   偶发成功窗口返回真实 JSON：`{"f57":"600519","f58":"贵州茅台","f116":1606517367893.1301,"f117":1606517367893.1301,"f127":"白酒Ⅱ"}`。
2. **日线 = `push2his.eastmoney.com` TLS 握手间歇失败**（直连与走代理均复现）：
   ```
   SSLError: HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded
   偶发: ProxyError
   ```
3. **代理因素**：本机 WinINET 启用了系统代理 `127.0.0.1:7892`（Clash），`requests` 默认 `trust_env=True` 会对所有主机使用该代理；该代理对 `push2*.eastmoney.com` 不稳定（SSL/Proxy/502），而 `search-api-web` 稳定。
   验证：`requests.utils.get_environ_proxies('<host>')` 返回 `{'https': 'http://127.0.0.1:7892'}`。

## 3.1 重要线索：延迟行情主机可用

实测 `push2.eastmoney.com` 连续 20 次 HTTP 502 时，同族**延迟行情主机 `push2delay.eastmoney.com` 返回 HTTP 200**，同一接口给出 600519 真实数据（贵州茅台 / 白酒Ⅱ / 总市值·流通市值）。
→ 股票基础信息的实时获取可考虑切到 `push2delay` 主机（或在其恢复前用它做只读快照采集，本次冻结包的股票快照即由此采集，证据见包内 `stock_basic_600519.raw.json` 与 provenance）。

## 4. 不含凭据的配置建议

- **优先**：确认本地代理（Clash `127.0.0.1:7892`）正常运行，且对其规则/节点到 `*.eastmoney.com`、`*.sina.com.cn` 稳定；`push2*` 与 `search-api-web` 需分别可用。
- 若存在**直连可用**的通路，可对这两个域**绕过代理**（`NO_PROXY=eastmoney.com,sina.com.cn`）；本环境实测直连同样失败，需按实际网络确认。
- **重试**：这两类失败为间歇性，建议调用侧对 `StockDataProviderError` 做有限次数重试（B 的冻结/实时入口已按请求级；是否在 Provider 内加重试待与 D 确认）。
- **不要**把数据源错误降级为空数据；B 保持 `50001`。

## 5. 契约

- 两个接口失败均抛 `StockDataProviderError` → HTTP `50001`（`data provider error`），`ai_analysis` 不落库。
- 未修改 C 量化算法、A 前端源码。

## 6. 冻结链路不受影响

实时端点不可用时，**冻结样本链路**（本地文件 → `ai_quant_test` → 量化）完全离线可跑，B/C 已完成一致性验证；
实时 AKShare 冒烟待上述网络/代理问题解决后单独记录。

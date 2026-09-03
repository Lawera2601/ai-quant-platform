// 按 docs/API_SPEC.md 的数据格式造 mock，后端接口就绪后 VITE_USE_MOCK=false 即可切换
import type {
  ApiResponse,
  BacktestData,
  IndicatorsItem,
  KlineItem,
  ScoreData,
  StockBrief,
} from '../types/api'

const STOCK_LIST: StockBrief[] = [
  { stock_code: '600519', stock_name: '贵州茅台' },
  { stock_code: '000858', stock_name: '五粮液' },
  { stock_code: '000568', stock_name: '泸州老窖' },
  { stock_code: '600809', stock_name: '山西汾酒' },
  { stock_code: '600036', stock_name: '招商银行' },
  { stock_code: '601318', stock_name: '中国平安' },
  { stock_code: '300750', stock_name: '宁德时代' },
  { stock_code: '002594', stock_name: '比亚迪' },
  { stock_code: '300059', stock_name: '东方财富' },
  { stock_code: '601012', stock_name: '隆基绿能' },
]

export function mockSearch(keyword: string): ApiResponse<StockBrief[]> {
  const kw = keyword.trim()
  const data = kw
    ? STOCK_LIST.filter(
        (item) => item.stock_code.includes(kw) || item.stock_name.includes(kw),
      )
    : STOCK_LIST
  return { code: 0, message: 'success', data }
}

// 固定种子的伪随机数，保证每次刷新数据一致，方便演示和调试
function mulberry32(seed: number) {
  return () => {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function buildDates(count: number, endDate = new Date('2026-09-02')): string[] {
  const dates: string[] = []
  const cursor = new Date(endDate)
  while (dates.length < count) {
    const day = cursor.getDay()
    if (day !== 0 && day !== 6) {
      dates.unshift(cursor.toISOString().slice(0, 10))
    }
    cursor.setDate(cursor.getDate() - 1)
  }
  return dates
}

function buildKline(days: number, seed: number, basePrice: number): KlineItem[] {
  const rand = mulberry32(seed)
  const dates = buildDates(days)
  let close = basePrice
  const rows: KlineItem[] = []
  for (const trade_date of dates) {
    const open = close * (1 + (rand() - 0.5) * 0.01)
    const changePct = (rand() - 0.48) * 0.045
    close = open * (1 + changePct)
    const high = Math.max(open, close) * (1 + rand() * 0.012)
    const low = Math.min(open, close) * (1 - rand() * 0.012)
    const volume = Math.round(30000 + rand() * 90000)
    rows.push({
      trade_date,
      open: round2(open),
      high: round2(high),
      low: round2(low),
      close: round2(close),
      volume,
      amount: round2(volume * close * 100),
      turnover_rate: Number((volume / 1_200_000_000).toFixed(4)),
      change_pct: Number(changePct.toFixed(4)),
    })
  }
  return rows
}

function round2(value: number): number {
  return Number(value.toFixed(2))
}

function average(values: number[], count: number): number {
  const slice = values.slice(-count)
  return slice.reduce((sum, value) => sum + value, 0) / slice.length
}

function stdDev(values: number[]): number {
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length
  const variance =
    values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length
  return Math.sqrt(variance)
}

export function mockKline(days = 180): ApiResponse<KlineItem[]> {
  return { code: 0, message: 'success', data: buildKline(days, 20260902, 1350) }
}

export function mockIndicators(): ApiResponse<IndicatorsItem[]> {
  const kline = buildKline(180, 20260902, 1350)
  const data: IndicatorsItem[] = kline.map((row, index) => {
    const closes = kline.slice(0, index + 1).map((item) => item.close)
    const ma20 = average(closes, Math.min(20, closes.length))
    const std = stdDev(closes.slice(-20)) || 1
    return {
      trade_date: row.trade_date,
      ma5: round2(average(closes, Math.min(5, closes.length))),
      ma10: round2(average(closes, Math.min(10, closes.length))),
      ma20: round2(ma20),
      ma60: round2(average(closes, Math.min(60, closes.length))),
      macd: Number(((row.close - ma20) / 8).toFixed(3)),
      macd_signal: Number(((row.close - ma20) / 10).toFixed(3)),
      macd_hist: Number(((row.close - ma20) / 40).toFixed(3)),
      rsi14: Number((35 + std * 2).toFixed(2)),
      boll_upper: round2(ma20 + 2 * std),
      boll_middle: round2(ma20),
      boll_lower: round2(ma20 - 2 * std),
    }
  })
  return { code: 0, message: 'success', data }
}

export function mockScore(stockCode: string): ApiResponse<ScoreData> {
  return {
    code: 0,
    message: 'success',
    data: {
      stock_code: stockCode,
      score: 72,
      trend_score: 30,
      momentum_score: 18,
      volume_score: 12,
      risk_score: 12,
      level: 'B',
      reasons: [
        '价格站上 MA20，短期趋势偏多',
        'RSI14 处于中性区间，未超买',
        '成交量温和放大，量价配合',
        '近期回撤可控，风险得分中等',
      ],
    },
  }
}

export function mockBacktest(stockCode: string): ApiResponse<BacktestData> {
  const kline = buildKline(180, 20260902, 1350)
  const first = kline[0].close
  return {
    code: 0,
    message: 'success',
    data: {
      backtest_id: `mock-${stockCode}`,
      stock_code: stockCode,
      metrics: {
        total_return: 0.153,
        annual_return: 0.21,
        max_drawdown: -0.12,
        sharpe: 1.36,
        win_rate: 0.54,
        trade_count: 23,
      },
      equity_curve: kline.map((row) => ({
        trade_date: row.trade_date,
        value: Number((row.close / first).toFixed(4)),
      })),
    },
  }
}

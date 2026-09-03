// 字段均按 docs/API_SPEC.md 契约定义，契约变更时需同步团队
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface HealthData {
  status: 'ok' | string
}

// GET /stocks/search
export interface StockBrief {
  stock_code: string
  stock_name: string
}

// GET /stocks/{stock_code}/kline（日期 YYYY-MM-DD，百分比用小数）
export interface KlineItem {
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  turnover_rate: number
  change_pct: number
}

// GET /stocks/{stock_code}/indicators
export interface IndicatorsItem {
  trade_date: string
  ma5: number
  ma10: number
  ma20: number
  ma60: number
  macd: number
  macd_signal: number
  macd_hist: number
  rsi14: number
  boll_upper: number
  boll_middle: number
  boll_lower: number
}

// GET /stocks/{stock_code}/score（分项上限 40/25/20/15，总分 0-100）
export interface ScoreData {
  stock_code: string
  score: number
  trend_score: number
  momentum_score: number
  volume_score: number
  risk_score: number
  level: string
  reasons: string[]
}

// POST /ai/analyze
export type TrendValue = 'bullish' | 'neutral' | 'bearish'

export interface AIAnalysisData {
  stock_code: string
  quant_score: number | null
  trend: TrendValue
  summary: string
  technical_analysis: string
  quant_analysis: string
  news_analysis: string
  advantages: string[]
  risks: string[]
  conclusion: string
  model_name: string
}

// POST /backtests（SPEC 未定死字段，equity_curve 待团队确认，先保留最小结构）
export interface BacktestData {
  backtest_id: string
  stock_code: string
  metrics: Record<string, number>
  equity_curve?: Array<{ trade_date: string; value: number }>
}

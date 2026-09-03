import { http } from './http'
import { mockBacktest, mockIndicators, mockKline, mockScore, mockSearch } from '../mocks/stock'
import type {
  ApiResponse,
  BacktestData,
  IndicatorsItem,
  KlineItem,
  ScoreData,
  StockBrief,
} from '../types/api'

// 后端未就绪的接口走 mock，VITE_USE_MOCK=false 或删除后切回真实请求
const useMock = import.meta.env.VITE_USE_MOCK === 'true'

export async function searchStocks(keyword: string): Promise<ApiResponse<StockBrief[]>> {
  if (useMock) return mockSearch(keyword)
  const response = await http.get<ApiResponse<StockBrief[]>>('/stocks/search', {
    params: { keyword },
  })
  return response.data
}

export async function fetchKline(
  stockCode: string,
  params: { start_date?: string; end_date?: string } = {},
): Promise<ApiResponse<KlineItem[]>> {
  if (useMock) return mockKline()
  const response = await http.get<ApiResponse<KlineItem[]>>(
    `/stocks/${stockCode}/kline`,
    { params },
  )
  return response.data
}

export async function fetchIndicators(
  stockCode: string,
): Promise<ApiResponse<IndicatorsItem[]>> {
  if (useMock) return mockIndicators()
  const response = await http.get<ApiResponse<IndicatorsItem[]>>(
    `/stocks/${stockCode}/indicators`,
  )
  return response.data
}

export async function fetchScore(stockCode: string): Promise<ApiResponse<ScoreData>> {
  if (useMock) return mockScore(stockCode)
  const response = await http.get<ApiResponse<ScoreData>>(`/stocks/${stockCode}/score`)
  return response.data
}

export async function runBacktest(stockCode: string): Promise<ApiResponse<BacktestData>> {
  if (useMock) return mockBacktest(stockCode)
  const response = await http.post<ApiResponse<BacktestData>>('/backtests', {
    stock_code: stockCode,
  })
  return response.data
}

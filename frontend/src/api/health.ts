import { http } from './http'
import type { ApiResponse, HealthData } from '../types/api'

export async function fetchHealth(): Promise<ApiResponse<HealthData>> {
  // 健康检查自带状态标签展示，跳过全局错误弹窗
  const response = await http.get<ApiResponse<HealthData>>('/health', {
    skipErrorHandler: true,
  })
  return response.data
}

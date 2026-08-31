import { http } from './http'
import type { ApiResponse, HealthData } from '../types/api'

export async function fetchHealth(): Promise<ApiResponse<HealthData>> {
  const response = await http.get<ApiResponse<HealthData>>('/health')
  return response.data
}

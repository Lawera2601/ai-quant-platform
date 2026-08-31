export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface HealthData {
  status: 'ok' | string
}

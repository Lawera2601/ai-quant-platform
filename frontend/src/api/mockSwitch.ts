// 分接口 Mock 开关：VITE_USE_MOCK_<接口名>（如 VITE_USE_MOCK_KLINE）优先；
// 未设置时回退全局 VITE_USE_MOCK。联调时把已就绪的接口单独改为 false，其余保留 mock。
export function useMockFor(apiName: string): boolean {
  const env = import.meta.env as Record<string, string | undefined>
  const perApi = env[`VITE_USE_MOCK_${apiName}`]
  if (perApi !== undefined) return perApi === 'true'
  return env.VITE_USE_MOCK === 'true'
}

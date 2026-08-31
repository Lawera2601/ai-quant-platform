import { computed, reactive } from 'vue'

import { fetchHealth } from '../api/health'

const state = reactive({
  status: 'unknown',
  loading: false,
  error: '',
})

export function useHealthStore() {
  async function refresh() {
    state.loading = true
    state.error = ''
    try {
      const result = await fetchHealth()
      state.status = result.data.status
    } catch (error) {
      state.status = 'unavailable'
      state.error = error instanceof Error ? error.message : 'health check failed'
    } finally {
      state.loading = false
    }
  }

  return {
    status: computed(() => state.status),
    loading: computed(() => state.loading),
    error: computed(() => state.error),
    refresh,
  }
}

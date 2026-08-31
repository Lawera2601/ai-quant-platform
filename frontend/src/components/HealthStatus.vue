<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useHealthStore } from '../stores/health'

const health = useHealthStore()
const tagType = computed(() => (health.status === 'ok' ? 'success' : 'warning'))

onMounted(() => {
  void health.refresh()
})
</script>

<template>
  <section class="health-panel">
    <div>
      <p class="eyebrow">Backend Health</p>
      <h2>FastAPI 联通状态</h2>
    </div>
    <el-tag :type="tagType" effect="dark">
      {{ health.loading ? 'checking' : health.status }}
    </el-tag>
    <p v-if="health.error" class="error-text">{{ health.error }}</p>
    <el-button size="small" :loading="health.loading" @click="health.refresh">
      重新检测
    </el-button>
  </section>
</template>

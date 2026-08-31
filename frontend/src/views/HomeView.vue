<script setup lang="ts">
import HealthStatus from '../components/HealthStatus.vue'
</script>

<template>
  <main class="shell">
    <section class="workspace">
      <div class="intro">
        <p class="eyebrow">AI Quant Research Platform V1</p>
        <h1>智能量化投研基础工程</h1>
        <p>
          当前版本只初始化工程骨架与后端健康检查，为后续股票搜索、真实行情、指标、评分、回测和 AI 分析保留稳定边界。
        </p>
      </div>

      <HealthStatus />

      <section class="module-grid" aria-label="V1 modules">
        <article>AKShare Provider</article>
        <article>MySQL 8</article>
        <article>FastAPI</article>
        <article>Vue 3</article>
      </section>
    </section>
  </main>
</template>

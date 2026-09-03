<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { fetchIndicators, fetchKline, fetchScore, runBacktest } from '../api/stocks'
import type { BacktestData, IndicatorsItem, KlineItem, ScoreData } from '../types/api'
import KlineChart from '../components/stock/KlineChart.vue'
import AIReportCard from '../components/ai/AIReportCard.vue'
import ScoreCard from '../components/stock/ScoreCard.vue'
import BacktestPanel from '../components/stock/BacktestPanel.vue'

const router = useRouter()
const stockCode = computed(() => String(router.currentRoute.value.params.code ?? ''))

const kline = ref<KlineItem[]>([])
const indicators = ref<IndicatorsItem[]>([])
const score = ref<ScoreData | null>(null)
const backtest = ref<BacktestData | null>(null)
const loading = ref(false)
const loaded = ref(false)
const scoreLoading = ref(true)
const backtestLoading = ref(true)

const latest = computed(() =>
  kline.value.length > 0 ? kline.value[kline.value.length - 1] : null,
)
const lastChange = computed(() => latest.value?.change_pct ?? 0)
const changeText = computed(() => {
  const sign = lastChange.value > 0 ? '▲' : lastChange.value < 0 ? '▼' : ''
  const value = `${(lastChange.value * 100).toFixed(2)}%`
  return `${sign} ${value}`.trim()
})
const changeClass = computed(() =>
  lastChange.value > 0 ? 'up' : lastChange.value < 0 ? 'down' : '',
)

async function load() {
  if (!stockCode.value) return
  loading.value = true
  loaded.value = false
  kline.value = []
  indicators.value = []
  try {
    // K 线是主请求；指标失败只降级（图上不画 MA/MACD），不影响 K 线展示
    const klineRes = await fetchKline(stockCode.value)
    kline.value = klineRes.data
    loaded.value = true
    fetchIndicators(stockCode.value)
      .then((res) => (indicators.value = res.data))
      .catch(() => undefined)
  } catch {
    // 拦截器已统一弹错误提示
  } finally {
    loading.value = false
  }

  // 评分/回测异步加载：失败只隐藏对应卡片，不影响主链路
  scoreLoading.value = true
  backtestLoading.value = true
  fetchScore(stockCode.value)
    .then((res) => (score.value = res.data))
    .catch(() => undefined)
    .finally(() => (scoreLoading.value = false))
  runBacktest(stockCode.value)
    .then((res) => (backtest.value = res.data))
    .catch(() => undefined)
    .finally(() => (backtestLoading.value = false))
}

watch(stockCode, load, { immediate: true })
</script>

<template>
  <main class="shell">
    <section class="workspace">
      <header class="detail-header">
        <el-button text @click="router.back()">← 返回</el-button>
        <div class="title">
          <h2>{{ stockCode }} 日 K 线（前复权）</h2>
          <div v-if="latest" class="quote">
            <span class="price">{{ latest.close.toFixed(2) }}</span>
            <span :class="['change', changeClass]">{{ changeText }}</span>
            <span class="date">{{ latest.trade_date }}</span>
          </div>
        </div>
      </header>

      <el-card v-loading="loading" shadow="never" class="card-lift chart-card">
        <KlineChart
          v-if="loaded && kline.length > 0"
          :items="kline"
          :indicators="indicators"
        />
        <el-empty v-else-if="loaded" description="暂无 K 线数据" />
      </el-card>

      <AIReportCard :stock-code="stockCode" />

      <div class="bottom-grid">
        <!-- 成功渲染卡片，加载中显示骨架，失败静默隐藏 -->
        <ScoreCard v-if="score" :data="score" />
        <el-card v-else-if="scoreLoading" shadow="never" class="card-lift">
          <el-skeleton :rows="4" animated />
        </el-card>

        <BacktestPanel v-if="backtest" :data="backtest" />
        <el-card v-else-if="backtestLoading" shadow="never" class="card-lift">
          <el-skeleton :rows="4" animated />
        </el-card>
      </div>
    </section>
  </main>
</template>

<style scoped>
.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border, rgba(255, 255, 255, 0.07));
}

.title {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 16px;
}

.title h2 {
  margin: 0;
}

.quote {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.price {
  font-size: 30px;
  font-weight: 700;
  color: var(--text-main);
}

.change {
  font-size: 15px;
  font-weight: 700;
}

.change.up {
  color: var(--up);
}

.change.down {
  color: var(--down);
}

.date {
  color: var(--text-faint);
  font-size: 13px;
}

.chart-card {
  margin-bottom: 16px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 900px) {
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { searchStocks } from '../api/stocks'
import type { StockBrief } from '../types/api'
import HealthStatus from '../components/HealthStatus.vue'

const router = useRouter()
const keyword = ref('')
const results = ref<StockBrief[]>([])
const loading = ref(false)
const searched = ref(false)

async function onSearch() {
  loading.value = true
  try {
    const res = await searchStocks(keyword.value)
    results.value = res.data
    searched.value = true
  } catch {
    // 拦截器已统一弹错误提示，这里只收敛异常
  } finally {
    loading.value = false
  }
}

function goDetail(stock: StockBrief) {
  router.push(`/stock/${stock.stock_code}`)
}
</script>

<template>
  <main class="shell">
    <section class="workspace">
      <div class="intro">
        <p class="eyebrow">AI Quant Research Platform V1</p>
        <h1>智能量化投研平台</h1>
        <p>搜索一只股票，查看真实 K 线、技术指标与 AI 投研分析。</p>
      </div>

      <HealthStatus />

      <section class="search-panel">
        <el-input
          v-model="keyword"
          size="large"
          placeholder="输入股票代码或名称，如 600519 / 茅台"
          clearable
          @keyup.enter="onSearch"
        >
          <template #append>
            <el-button :loading="loading" @click="onSearch">搜索</el-button>
          </template>
        </el-input>

        <el-empty
          v-if="searched && results.length === 0"
          description="没有找到匹配的股票"
        />

        <ul v-else-if="results.length > 0" class="result-list">
          <li v-for="stock in results" :key="stock.stock_code">
            <button type="button" class="result-item" @click="goDetail(stock)">
              <span class="stock-name">{{ stock.stock_name }}</span>
              <span class="stock-code">{{ stock.stock_code }}</span>
            </button>
          </li>
        </ul>

        <p v-if="searched && results.length > 0" class="result-hint">
          共 {{ results.length }} 条结果，点击进入股票详情
        </p>
      </section>
    </section>
  </main>
</template>

<style scoped>
.search-panel {
  margin-top: 28px;
  padding: 22px;
  border: 1px solid var(--border, rgba(255, 255, 255, 0.07));
  border-radius: 8px;
  background: var(--surface, #14171d);
}

.result-list {
  list-style: none;
  margin: 16px 0 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.result-item {
  display: flex;
  width: 100%;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border: 1px solid var(--border, rgba(255, 255, 255, 0.07));
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  font: inherit;
  color: inherit;
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}

.result-item:hover {
  border-color: var(--border-strong, rgba(255, 255, 255, 0.16));
  background: var(--surface-hover, #181c23);
}

.stock-name {
  font-weight: 600;
}

.stock-code {
  color: var(--text-faint, rgba(255, 255, 255, 0.38));
  font-variant-numeric: tabular-nums;
}

.result-hint {
  margin: 12px 0 0;
  color: var(--text-faint, rgba(255, 255, 255, 0.38));
  font-size: 13px;
}

@media (max-width: 760px) {
  .result-list {
    grid-template-columns: 1fr;
  }
}
</style>

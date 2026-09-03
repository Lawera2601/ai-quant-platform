import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/stock/:code',
      name: 'stock-detail',
      // 路由复用同一组件实例时（如 /stock/A → /stock/B）需要重新拉数据
      component: () => import('../views/StockDetailView.vue'),
    },
    {
      // 未匹配路径一律回首页
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

export default router

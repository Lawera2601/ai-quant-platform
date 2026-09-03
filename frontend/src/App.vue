<template>
  <div class="app-frame">
    <header class="top-bar">
      <router-link to="/" class="brand">
        <span class="brand-mark" aria-hidden="true"></span>
        <span class="brand-name">智能量化投研平台</span>
      </router-link>
      <span class="brand-sub">AI Quant Research</span>
    </header>
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style scoped>
.app-frame {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 54px;
  padding: 0 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(14, 17, 22, 0.9);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.brand-mark {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  background: var(--accent, #d4a958);
}

.brand-name {
  color: rgba(255, 255, 255, 0.92);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.brand-sub {
  color: rgba(255, 255, 255, 0.38);
  font-size: 12px;
  letter-spacing: 0.08em;
}

@media (max-width: 760px) {
  .top-bar {
    padding: 0 16px;
  }

  .brand-sub {
    display: none;
  }
}
</style>

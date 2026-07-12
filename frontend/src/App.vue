<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from './stores/app'
import MessageListener from './components/common/MessageListener.vue'
import { NMessageProvider, NDialogProvider } from 'naive-ui'
import { LayoutDashboard, BookOpen, Share2, Search, Database, BarChart3, Bot, Settings, Sparkles } from '@lucide/vue'

const router = useRouter()
const route = useRoute()
const store = useAppStore()

const menuItems = [
  { label: '总览', key: '/', icon: LayoutDashboard },
  { label: '知识库', key: '/knowledge', icon: BookOpen },
  { label: '知识图谱', key: '/graph', icon: Share2 },
  { label: '搜索日志', key: '/search-log', icon: Search },
  { label: '数据库', key: '/database', icon: Database },
  { label: '统计', key: '/analytics', icon: BarChart3 },
  { label: 'MCP 服务', key: '/mcp', icon: Bot },
  { label: '设置', key: '/settings', icon: Settings },
]

const pageTitles: Record<string, string> = {
  Dashboard: '总览', Knowledge: '知识库', KnowledgeDetail: '知识详情',
  Graph: '知识图谱', SearchLog: '搜索日志',
  Database: '数据库', Analytics: '统计分析', MCP: 'MCP 服务', Settings: '设置'
}

const activeKey = computed(() => route.path)
const pageTitle = computed(() => pageTitles[route.name as string] || route.name || '')

function navigate(key: string) { router.push(key) }
</script>

<template>
  <NMessageProvider>
    <NDialogProvider>
      <MessageListener />
      <div class="app-layout">
        <aside :class="['app-sidebar', { collapsed: store.sidebarCollapsed }]">
          <div class="sidebar-logo">
            <svg class="logo-icon" width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
              <!-- Outer ring -->
              <circle cx="14" cy="14" r="12" stroke="url(#logo-gradient)" stroke-width="1.2" />
              <!-- Center dot -->
              <circle cx="14" cy="14" r="2.5" fill="url(#logo-gradient)" />
              <!-- Orbiting dots -->
              <circle cx="14" cy="4" r="1.2" fill="url(#logo-gradient)" opacity="0.6" />
              <circle cx="24" cy="14" r="1.2" fill="url(#logo-gradient)" opacity="0.6" />
              <circle cx="14" cy="24" r="1.2" fill="url(#logo-gradient)" opacity="0.6" />
              <circle cx="4" cy="14" r="1.2" fill="url(#logo-gradient)" opacity="0.6" />
              <!-- Connection lines -->
              <line x1="14" y1="4" x2="14" y2="11.5" stroke="url(#logo-gradient)" stroke-width="0.8" opacity="0.4" />
              <line x1="24" y1="14" x2="16.5" y2="14" stroke="url(#logo-gradient)" stroke-width="0.8" opacity="0.4" />
              <line x1="14" y1="24" x2="14" y2="16.5" stroke="url(#logo-gradient)" stroke-width="0.8" opacity="0.4" />
              <line x1="4" y1="14" x2="11.5" y2="14" stroke="url(#logo-gradient)" stroke-width="0.8" opacity="0.4" />
              <defs>
                <linearGradient id="logo-gradient" x1="0" y1="0" x2="28" y2="28">
                  <stop offset="0%" stop-color="#0071e3" />
                  <stop offset="100%" stop-color="#5856d6" />
                </linearGradient>
              </defs>
            </svg>
            <span class="logo-text">AI 鐭ヨ瘑涓績</span>
          </div>
          <nav class="sidebar-nav">
            <a v-for="item in menuItems" :key="item.key"
               :class="['nav-item', { active: activeKey === item.key }]"
               @click="navigate(item.key)">
              <component :is="item.icon" :size="20" class="nav-icon" stroke-width="1.5" />
              <span class="nav-label">{{ item.label }}</span>
            </a>
          </nav>
          <div class="sidebar-toggle" @click="store.sidebarCollapsed = !store.sidebarCollapsed">
            <span v-if="!store.sidebarCollapsed">鈼€</span>
            <span v-else>鈻?</span>
          </div>
        </aside>
        <div class="app-main">
          <header class="app-header">
            <h1>{{ pageTitle }}</h1>
          </header>
          <main class="app-content">
            <router-view />
          </main>
        </div>
      </div>
    </NDialogProvider>
  </NMessageProvider>
</template>
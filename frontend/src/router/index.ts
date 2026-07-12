import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/dashboard/Index.vue') },
  { path: '/knowledge', name: 'Knowledge', component: () => import('../views/knowledge/Index.vue') },
  { path: '/knowledge/:id', name: 'KnowledgeDetail', component: () => import('../views/knowledge/Detail.vue') },
  { path: '/collections', name: 'Collections', component: () => import('../views/collections/Index.vue') },
  { path: '/graph', name: 'Graph', component: () => import('../views/graph/Index.vue') },
  { path: '/search-log', name: 'SearchLog', component: () => import('../views/search-log/Index.vue') },
  { path: '/database', name: 'Database', component: () => import('../views/database/Index.vue') },
  { path: '/analytics', name: 'Analytics', component: () => import('../views/analytics/Index.vue') },
  { path: '/mcp', name: 'MCP', component: () => import('../views/mcp/Index.vue') },
  { path: '/settings', name: 'Settings', component: () => import('../views/settings/Index.vue') },
]

export default createRouter({ history: createWebHashHistory(), routes })

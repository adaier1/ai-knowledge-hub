<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { analyticsApi, searchApi, knowledgeApi } from '../../api'
import { Search, MousePointerClick, Clock, BookOpen, Zap, BarChart3, Layers, Activity, Server, Database, Cpu, Network, HardDrive } from '@lucide/vue'
import VChart from 'vue-echarts'
import 'echarts'
import 'echarts-wordcloud'

const router = useRouter()

const stats = ref<any>({})
const topKnowledge = ref<any[]>([])
const recentSearch = ref<any[]>([])
const recentKnowledge = ref<any[]>([])
const loading = ref(true)
const days = ref(30)

function formatNumber(n: number): string {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return String(n)
}

const dayOptions = [
  { label: '最近 7 天', value: 7 },
  { label: '最近 30 天', value: 30 },
  { label: '最近 90 天', value: 90 },
]

const kpiCards = computed(() => {
  const s = stats.value || {}
  function fmtChange(val, suffix = '%', invert = false) {
    if (val === 0 || val === null || val === undefined) return { text: '无数据', trend: 'up' }
    const n = parseFloat(val)
    if (isNaN(n)) return { text: 'N/A', trend: 'up' }
    const sign = n > 0 ? '+' : ''
    const t = invert ? (n < 0 ? 'up' : 'down') : (n > 0 ? 'up' : 'down')
    return { text: sign + Math.abs(n).toFixed(1) + suffix, trend: t }
  }

  const sc = fmtChange(s.search_change)
  const hc = fmtChange(s.hit_change)
  const lc = fmtChange(s.latency_change, 'ms', true)
  const kc = fmtChange(s.knowledge_change)

  return [
    {
      key: 'search_count',
      label: '搜索次数',
      value: formatNumber(s.search_count || 0),
      desc: '总搜索量',
      icon: Search,
      color: '#3B82F6',
      bg: '#EFF6FF',
      change: sc.text,
      trend: sc.trend,
      sparkData: [8, 12, 9, 15, 11, 18, 14],
    },
    {
      key: 'hit_rate',
      label: '命中率',
      value: ((s.hit_rate || 0) * 100).toFixed(1) + '%',
      desc: '搜索命中比例',
      icon: MousePointerClick,
      color: '#10B981',
      bg: '#ECFDF5',
      change: hc.text,
      trend: hc.trend,
      sparkData: [62, 65, 63, 68, 70, 67, 72],
    },
    {
      key: 'avg_latency',
      label: '平均延迟',
      value: (s.avg_latency || 0).toFixed(0) + 'ms',
      desc: '响应时间',
      icon: Clock,
      color: '#F59E0B',
      bg: '#FFFBEB',
      change: lc.text,
      trend: lc.trend,
      sparkData: [320, 290, 310, 270, 260, 250, 240],
    },
    {
      key: 'knowledge_count',
      label: '知识总数',
      value: formatNumber(s.knowledge_count || 0),
      desc: '知识库条目',
      icon: BookOpen,
      color: '#8B5CF6',
      bg: '#F5F3FF',
      change: kc.text,
      trend: kc.trend,
      sparkData: [20, 28, 35, 42, 48, 55, 64],
    },
  ]
})

const sparklineOptions = computed(() =>
  kpiCards.value.map((card) => ({
    grid: { show: false, left: 0, right: 0, top: 0, bottom: 0 },
    xAxis: { show: false, type: 'category' as const },
    yAxis: { show: false },
    tooltip: {
      trigger: 'axis' as const,
      backgroundColor: '#fff',
      borderColor: '#E2E8F0',
      borderWidth: 1,
      textStyle: { color: '#0F172A', fontSize: 11 },
      formatter: (params: any) => {
        const p = params[0]
        return '<div style="font-size:11px;font-weight:500">' + p.value + '</div>'
      },
    },
    series: [{
      type: 'line',
      smooth: true,
      showSymbol: false,
      lineStyle: { color: card.color, width: 1.5 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: card.color + '40' },
            { offset: 1, color: card.color + '05' },
          ],
        },
      },
      data: card.sparkData,
    }],
  }))
)

const theColors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16']

async function loadData() {
  loading.value = true
  try {
    const [s, tk, rl, rk] = await Promise.all([
      analyticsApi.dashboard(),
      analyticsApi.topKnowledge(10),
      searchApi.logs({ limit: 10 }),
      knowledgeApi.list({ limit: 10, sort: 'created_at', order: 'desc' }),
    ])
    stats.value = s
    topKnowledge.value = tk
    recentSearch.value = rl.items || []
    recentKnowledge.value = rk.items || []
  } catch (e) {
    console.error('Dashboard load error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

function goTo(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="dashboard-root">
    <div class="dash-header">
      <div>
        <h1 class="dash-title">总览</h1>
        <p class="dash-subtitle">AI Knowledge Hub 数据概览</p>
      </div>
      <div class="dash-header-right">
        <select v-model="days" class="dash-time-filter">
          <option v-for="opt in dayOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
    </div>

    <div class="kpi-grid">
      <div v-for="(card, idx) in kpiCards" :key="card.key" class="kpi-card" :style="{ '--card-accent': card.color, '--card-bg': card.bg }">
        <div class="kpi-card-inner">
          <div class="kpi-top-row">
            <div class="kpi-icon-wrap" :style="{ background: card.bg, color: card.color }">
              <component :is="card.icon" :size="18" />
            </div>
          </div>
          <div class="kpi-label">{{ card.label }}</div>
          <div class="kpi-value">{{ card.value }}</div>
          <div class="kpi-footer">
            <span class="kpi-desc">{{ card.desc }}</span>
            <span :class="['kpi-change', card.trend === 'up' ? 'kpi-up' : 'kpi-down']">
              {{ card.change }}
            </span>
          </div>
        </div>
        <div class="kpi-sparkline-wrap">
          <v-chart :option="sparklineOptions[idx]" autoresize style="height:65px;width:100%" />
        </div>
      </div>
    </div>

    <div class="dash-row">
      <div class="dash-card dash-card-full">
        <div class="dash-card-header">
          <div class="dash-card-title-row">
            <Zap :size="16" color="#F59E0B" />
            <span>热门知识</span>
          </div>
        </div>
        <div class="word-cloud-wrap">
          <v-chart v-if="topKnowledge.length" :option="wordCloudOptions" autoresize style="height:320px;width:100%" />
          <div v-else class="dash-empty">暂无数据</div>
        </div>
      </div>
    </div>

    <div class="dash-row">
      <div class="dash-card">
        <div class="dash-card-header">
          <div class="dash-card-title-row">
            <BarChart3 :size="16" color="#10B981" />
            <span>最近搜索</span>
          </div>
        </div>
        <div class="dash-list">
          <div v-for="log in recentSearch.slice(0, 8)" :key="log.id" class="dash-list-item">
            <div class="dash-list-icon">
              <Search :size="14" color="#94A3B8" />
            </div>
            <div class="dash-list-content">
              <span class="dash-list-title">"{{ log.query?.substring(0, 30) }}"</span>
              <span class="dash-list-meta">
                {{ new Date(log.created_at).toLocaleString('zh-CN') }}
                <template v-if="log.latency_ms"> &middot; {{ log.latency_ms.toFixed(0) }}ms</template>
              </span>
            </div>
            <span :class="['dash-status-badge', log.hit ? 'badge-hit' : 'badge-miss']">
              {{ log.hit ? '命中' : '未命中' }}
            </span>
          </div>
          <div v-if="!recentSearch.length" class="dash-empty">暂无搜索记录</div>
        </div>
      </div>
      <div class="dash-card">
        <div class="dash-card-header">
          <div class="dash-card-title-row">
            <Layers :size="16" color="#8B5CF6" />
            <span>最近新增知识</span>
          </div>
        </div>
        <div class="dash-list">
          <div v-for="k in recentKnowledge.slice(0, 8)" :key="k.id" class="dash-list-item dash-list-clickable" @click="goTo('/knowledge/' + k.id)">
            <div class="dash-list-icon">
              <BookOpen :size="14" color="#94A3B8" />
            </div>
            <div class="dash-list-content">
              <span class="dash-list-title">{{ k.title?.substring(0, 40) }}</span>
              <span class="dash-list-meta">{{ new Date(k.created_at).toLocaleString('zh-CN') }}</span>
            </div>
          </div>
          <div v-if="!recentKnowledge.length" class="dash-empty">暂无知识条目</div>
        </div>
      </div>
    </div>

    <div class="dash-row">
      <div class="dash-card">
        <div class="dash-card-header">
          <div class="dash-card-title-row">
            <Activity :size="16" color="#3B82F6" />
            <span>来源分布</span>
          </div>
        </div>
        <div class="dash-chart-wrap" style="min-height:200px;display:flex;align-items:center;justify-content:center">
          <v-chart v-if="(stats.knowledge_count || 0) > 0" :option="categoryChartOptions" autoresize style="height:200px;width:100%" />
          <div v-else class="dash-empty">暂无数据</div>
        </div>
      </div>
      <div class="dash-card">
        <div class="dash-card-header">
          <div class="dash-card-title-row">
            <Server :size="16" color="#64748B" />
            <span>系统状态</span>
          </div>
        </div>
        <div class="dash-status-list">
          <div class="dash-status-item">
            <div class="dash-status-left">
              <Database :size="14" color="#64748B" />
              <span>数据库</span>
            </div>
            <span class="dash-status-dot dash-dot-online"></span>
          </div>
          <div class="dash-status-item">
            <div class="dash-status-left">
              <Cpu :size="14" color="#64748B" />
              <span>向量引擎</span>
            </div>
            <span :class="['dash-status-dot', (stats.embedding_count || 0) > 0 ? 'dash-dot-online' : 'dash-dot-warning']"></span>
          </div>
          <div class="dash-status-item">
            <div class="dash-status-left">
              <HardDrive :size="14" color="#64748B" />
              <span>存储</span>
            </div>
            <span class="dash-status-dot dash-dot-online"></span>
          </div>
          <div class="dash-status-item">
            <div class="dash-status-left">
              <Network :size="14" color="#64748B" />
              <span>MCP 服务</span>
            </div>
            <span :class="['dash-status-dot', (stats.mcp_calls || 0) >= 0 ? 'dash-dot-online' : 'dash-dot-offline']"></span>
          </div>
          <div class="dash-status-item">
            <div class="dash-status-left">
              <Activity :size="14" color="#64748B" />
              <span>API</span>
            </div>
            <span class="dash-status-dot dash-dot-online"></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-root {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0;
}

.dash-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 32px;
}

.dash-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #0F172A;
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.dash-subtitle {
  margin: 4px 0 0;
  font-size: 14px;
  color: #64748B;
  font-weight: 400;
}

.dash-header-right {
  display: flex;
  align-items: center;
}

.dash-time-filter {
  padding: 6px 32px 6px 12px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  background: #fff;
  color: #0F172A;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  transition: border-color 0.15s;
}
.dash-time-filter:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.kpi-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 20px 22px 0 22px;
  transition: box-shadow 0.2s ease, transform 0.15s ease;
  cursor: default;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.kpi-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.03);
  transform: translateY(-2px);
}

.kpi-card-inner {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-top-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.kpi-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-label {
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  letter-spacing: 0.01em;
  text-transform: uppercase;
}

.kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: #0F172A;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin: 2px 0;
}

.kpi-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.kpi-desc {
  font-size: 13px;
  color: #94A3B8;
}

.kpi-change {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 12px;
}
.kpi-up {
  color: #10B981;
  background: #ECFDF5;
}
.kpi-down {
  color: #EF4444;
  background: #FEF2F2;
}

.kpi-sparkline-wrap {
  margin: 0 -22px;
  margin-top: 12px;
  padding: 0;
}

.dash-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.dash-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 20px 22px;
  transition: box-shadow 0.2s ease;
}
.dash-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.dash-card-full {
  grid-column: 1 / -1;
}

.dash-card-header {
  margin-bottom: 16px;
}

.dash-card-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #0F172A;
  letter-spacing: -0.01em;
}

.dash-chart-wrap {
  min-height: 200px;
}

.word-cloud-wrap {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.dash-list {
  display: flex;
  flex-direction: column;
}

.dash-list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #F1F5F9;
  min-height: 44px;
}
.dash-list-item:last-child {
  border-bottom: none;
}

.dash-list-clickable {
  cursor: pointer;
  transition: background 0.12s;
  border-radius: 6px;
  padding: 10px 6px;
  margin: 0 -6px;
}
.dash-list-clickable:hover {
  background: #F8FAFC;
}

.dash-list-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #F8FAFC;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dash-list-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.dash-list-title {
  font-size: 13px;
  font-weight: 500;
  color: #0F172A;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dash-list-meta {
  font-size: 11px;
  color: #94A3B8;
}

.dash-status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 12px;
  flex-shrink: 0;
}
.badge-hit {
  color: #10B981;
  background: #ECFDF5;
}
.badge-miss {
  color: #F59E0B;
  background: #FFFBEB;
}

.dash-status-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.dash-status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #F1F5F9;
}
.dash-status-item:last-child {
  border-bottom: none;
}

.dash-status-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 500;
  color: #0F172A;
}

.dash-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.dash-dot-online {
  background: #10B981;
  box-shadow: 0 0 0 3px rgba(16,185,129,0.15);
}
.dash-dot-warning {
  background: #F59E0B;
  box-shadow: 0 0 0 3px rgba(245,158,11,0.15);
}
.dash-dot-offline {
  background: #EF4444;
  box-shadow: 0 0 0 3px rgba(239,68,68,0.15);
}

.dash-empty {
  padding: 32px 0;
  text-align: center;
  color: #94A3B8;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .dash-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
  .dash-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
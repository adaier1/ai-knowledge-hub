<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { analyticsApi } from '../../api'
import { Search, MousePointerClick, Clock, BookOpen, BarChart3, ListOrdered, FileText, RefreshCw } from '@lucide/vue'
import VChart from 'vue-echarts'
import 'echarts'

const trends = ref<any[]>([])
const topQueries = ref<any[]>([])
const topKnowledge = ref<any[]>([])
const stats = ref<any>({})

const statCards = [
  { key: 'knowledge_count', label: '知识总量', icon: BookOpen, color: '#3B82F6', bg: '#EFF6FF' },
  { key: 'search_count', label: '搜索总量', icon: Search, color: '#10B981', bg: '#ECFDF5' },
  { key: 'hit_rate', label: '命中率', icon: MousePointerClick, color: '#F59E0B', bg: '#FFFBEB', fmt: (v: number) => (v * 100).toFixed(1) + '%' },
  { key: 'avg_latency', label: '平均延迟', icon: Clock, color: '#8B5CF6', bg: '#F5F3FF', fmt: (v: number) => v.toFixed(0) + 'ms' },
]

onMounted(async () => {
  try { stats.value = await analyticsApi.dashboard() } catch {}
  try { trends.value = await analyticsApi.trends(14) } catch {}
  try { topQueries.value = await analyticsApi.topQueries(10) } catch {}
  try { topKnowledge.value = await analyticsApi.topKnowledge(10) } catch {}
})

const logs = ref<any[]>([])
const logsLoading = ref(false)
const logLevel = ref('')

const filteredLogs = computed(() => {
  if (!logLevel.value) return logs.value
  return logs.value.filter(function(e) { return e.level === logLevel.value; })
})

async function loadLogs() {
  logsLoading.value = true
  try {
    const res = await fetch('/api/analytics/logs?lines=500')
    const data = await res.json()
    logs.value = data.logs || []
  } catch { logs.value = [] }
  finally { logsLoading.value = false }
}

onMounted(function() {
  setTimeout(loadLogs, 500)
})

const trendChartOptions = computed(() => {
  const dates = trends.value.map((t: any) => t.date?.substring(5) || '')
  const counts = trends.value.map((t: any) => t.count || 0)
  const hitRates = trends.value.map((t: any) => (t.hit_rate || 0) * 100)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 24, bottom: 24 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11, color: '#94A3B8' }, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisTick: { show: false } },
    yAxis: [
      { type: 'value', name: '搜索次数', nameTextStyle: { fontSize: 11, color: '#94A3B8' }, axisLabel: { fontSize: 11, color: '#94A3B8' }, splitLine: { lineStyle: { color: '#F1F5F9' } } },
      { type: 'value', name: '命中率 %', nameTextStyle: { fontSize: 11, color: '#94A3B8' }, axisLabel: { fontSize: 11, color: '#94A3B8', formatter: '{value}%' }, splitLine: { show: false } },
    ],
    series: [
      { name: '搜索次数', type: 'bar', data: counts, itemStyle: { color: '#3B82F6', borderRadius: [4,4,0,0] }, barWidth: '60%' },
      { name: '命中率', type: 'line', yAxisIndex: 1, data: hitRates, smooth: true, lineStyle: { color: '#10B981', width: 2 }, itemStyle: { color: '#10B981' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(16,185,129,0.15)' }, { offset: 1, color: 'rgba(16,185,129,0)' }] } } },
    ],
  }
})
</script>

<template>
  <div>
    <!-- KPI Stats -->
    <div class="kpi-grid">
      <div v-for="c in statCards" :key="c.key" class="dash-card" style="text-align:center;padding:20px 16px">
        <div :style="{width:40,height:40,borderRadius:10,background:c.bg,display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 10px'}">
          <component :is="c.icon" :size="20" :stroke-width="1.5" :color="c.color" />
        </div>
        <div style="font-size:12px;color:#64748B;margin-bottom:4px">{{ c.label }}</div>
        <div style="font-size:26px;font-weight:600;color:#0F172A;letter-spacing:-0.02em">
          {{ c.fmt ? c.fmt(stats[c.key] || 0) : (stats[c.key] || 0) }}
        </div>
      </div>
    </div>

    <!-- Trend & Top Queries -->
    <div class="dash-row">
      <div class="dash-card">
        <div class="dash-card-header">
          <div class="dash-card-title-row">
            <BarChart3 :size="16" stroke-width="1.5" color="#3B82F6" />
            <span>搜索趋势（14 天）</span>
          </div>
        </div>
        <div class="dash-chart-wrap" style="min-height:260px">
          <VChart v-if="trends.length" :option="trendChartOptions" autoresize style="height:260px" />
          <div v-else class="dash-empty">暂无趋势数据</div>
        </div>
      </div>
      <div>
        <div class="dash-card" style="margin-bottom:16px">
          <div class="dash-card-header">
            <div class="dash-card-title-row">
              <ListOrdered :size="16" stroke-width="1.5" color="#F59E0B" />
              <span>热门搜索</span>
            </div>
          </div>
          <div class="dash-list">
            <div v-for="q in topQueries" :key="q.query" class="dash-list-item">
              <div class="dash-list-content">
                <div class="dash-list-title">"{{ q.query?.substring(0, 40) }}"</div>
              </div>
              <strong style="font-size:14px;color:#0F172A">{{ q.count }}</strong>
            </div>
            <div v-if="!topQueries.length" class="dash-empty">暂无热门搜索</div>
          </div>
        </div>
        <div class="dash-card">
          <div class="dash-card-header">
            <div class="dash-card-title-row">
              <FileText :size="16" stroke-width="1.5" color="#10B981" />
              <span>热门知识</span>
            </div>
          </div>
          <div class="dash-list">
            <div v-for="k in topKnowledge" :key="k.id" class="dash-list-item">
              <div class="dash-list-content">
                <div class="dash-list-title">{{ k.title?.substring(0, 40) }}</div>
              </div>
              <strong style="font-size:14px;color:#0F172A">{{ k.count }}</strong>
            </div>
            <div v-if="!topKnowledge.length" class="dash-empty">暂无数据</div>
          </div>
        </div>
      </div>
    </div>

    <!-- System Logs -->
    <div class="dash-card">
      <div class="dash-card-header">
        <div style="display:flex;align-items:center;justify-content:space-between;width:100%">
          <div class="dash-card-title-row">
            <RefreshCw :size="16" stroke-width="1.5" color="#64748B" />
            <span>系统日志</span>
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            <select v-model="logLevel" style="padding:2px 8px;height:28px;border-radius:6px;border:1px solid #E2E8F0;font-size:12px;background:#fff;outline:none;color:#0F172A">
              <option value="">全部级别</option>
              <option value="ERROR">ERROR</option>
              <option value="WARNING">WARNING</option>
              <option value="INFO">INFO</option>
              <option value="DEBUG">DEBUG</option>
            </select>
            <button style="display:flex;align-items:center;gap:4px;padding:4px 12px;height:28px;border-radius:6px;border:1px solid #E2E8F0;background:#fff;font-size:12px;cursor:pointer;color:#0F172A" @click="loadLogs">
              <RefreshCw :size="12" stroke-width="1.5" :style="logsLoading ? 'animation:spin 1s linear infinite' : ''" />
              <span>{{ logsLoading ? '加载中' : '刷新' }}</span>
            </button>
          </div>
        </div>
      </div>
      <div v-if="filteredLogs.length === 0 && !logsLoading" class="dash-empty" style="padding:32px">暂无日志</div>
      <div v-else style="border:1px solid #E2E8F0;border-radius:10px;overflow:hidden">
        <table style="width:100%;border-collapse:collapse;font-size:12px">
          <thead>
            <tr style="background:#F8FAFC;border-bottom:1px solid #E2E8F0">
              <th style="padding:8px 12px;text-align:left;font-weight:600;color:#64748B;width:170px">时间</th>
              <th style="padding:8px 12px;text-align:left;font-weight:600;color:#64748B;width:70px">级别</th>
              <th style="padding:8px 12px;text-align:left;font-weight:600;color:#64748B">事件</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, idx) in filteredLogs.slice(0, 200)" :key="idx"
              style="border-bottom:1px solid #F1F5F9"
              :style="entry.level === 'ERROR' ? 'background:#FEF2F2' : entry.level === 'WARNING' ? 'background:#FFFBEB' : ''">
              <td style="padding:6px 12px;font-family:SF Mono,Menlo,monospace;color:#64748B;white-space:nowrap">{{ entry.time || '-' }}</td>
              <td style="padding:6px 12px">
                <span :style="{
                  display:'inline-block',padding:'1px 8px',borderRadius:'4px',fontSize:'11px',fontWeight:600,
                  color: entry.level === 'ERROR' ? '#DC2626' : entry.level === 'WARNING' ? '#D97706' : entry.level === 'INFO' ? '#2563EB' : '#78716C',
                  background: entry.level === 'ERROR' ? '#FEF2F2' : entry.level === 'WARNING' ? '#FFFBEB' : entry.level === 'INFO' ? '#EFF6FF' : '#F5F5F4'
                }">{{ entry.level }}</span>
              </td>
              <td style="padding:6px 12px;color:#1E293B;line-height:1.5;word-break:break-all">{{ entry.message || entry.raw }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="filteredLogs.length > 200" style="text-align:center;padding:12px;color:#94A3B8;font-size:12px">显示前 200 条，共 {{ filteredLogs.length }} 条</div>
    </div>
  </div>
</template>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg) }
  to { transform: rotate(360deg) }
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
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

.dash-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
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
}
</style>
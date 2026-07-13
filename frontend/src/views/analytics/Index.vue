<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NDataTable, NGrid, NGi, NNumberAnimation } from 'naive-ui'
import { analyticsApi } from '../../api'

const trends = ref<any[]>([])
const topQueries = ref<any[]>([])
const topKnowledge = ref<any[]>([])
const stats = ref<any>({})

const statCards = [
  { key: 'knowledge_count', label: '知识总量', icon: '📚' },
  { key: 'search_count', label: '搜索总量', icon: '🔍' },
  { key: 'hit_rate', label: '命中率', icon: '🎯', fmt: (v: number) => (v * 100).toFixed(1) + '%' },
  { key: 'avg_latency', label: '平均延迟', icon: '⚡', fmt: (v: number) => v.toFixed(0) + 'ms' },
]

onMounted(async () => {
  try { stats.value = await analyticsApi.dashboard() } catch {}
  try { trends.value = await analyticsApi.trends(14) } catch {}
  try { topQueries.value = await analyticsApi.topQueries(10) } catch {}
  try { topKnowledge.value = await analyticsApi.topKnowledge(10) } catch {}
})

const logs = ref<any[]>([])
const logsLoading = ref(false)

async function loadLogs() {
  logsLoading.value = true
  try {
    const res = await fetch('/api/analytics/logs?lines=200')
    const data = await res.json()
    logs.value = data.logs || []
  } catch { logs.value = [] }
  finally { logsLoading.value = false }
}

onMounted(() => {
  setTimeout(loadLogs, 500)
})

const trendColumns = [
  { title: '日期', key: 'date', width: 100 },
  { title: '搜索次数', key: 'count', width: 80 },
  { title: '命中率', key: 'hit_rate', width: 80, render: (r: any) => (r.hit_rate * 100).toFixed(1) + '%' },
  { title: '平均延迟', key: 'avg_latency', render: (r: any) => r.avg_latency.toFixed(0) + 'ms' },
]
</script>

<template>
  <div>
    <h2 class="text-xl font-bold mb-4">统计分析</h2>
    <NGrid :cols="4" :x-gap="12" :y-gap="12" style="margin-bottom:16px">
      <NGi v-for="c in statCards" :key="c.key">
        <NCard hoverable>
          <div style="text-align:center">
            <span style="font-size:28px">{{ c.icon }}</span>
            <div style="font-size:13px;color:#666;margin-top:4px">{{ c.label }}</div>
            <div style="font-size:24px;font-weight:bold;color:#18a058">
              <NNumberAnimation v-if="!c.fmt" :from="0" :to="stats[c.key] || 0" show-separator />
              <span v-else>{{ c.fmt(stats[c.key] || 0) }}</span>
            </div>
          </div>
        </NCard>
      </NGi>
    </NGrid>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <NCard title="搜索趋势（14 天）">
        <NDataTable :columns="trendColumns" :data="trends" size="small" max-height="300" />
      </NCard>
      <div>
        <NCard title="热门搜索" style="margin-bottom:12px">
          <div v-for="q in topQueries" :key="q.query" style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #eee">
            <span>"{{ q.query?.substring(0,40) }}"</span><strong>{{ q.count }}</strong>
          </div>
        </NCard>
        <NCard title="热门知识">
          <div v-for="k in topKnowledge" :key="k.id" style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #eee">
            <span>{{ k.title?.substring(0,40) }}</span><strong>{{ k.count }}</strong>
          </div>
        </NCard>
      </div>
    </div>
    <!-- Log Viewer -->
  <div style="margin-top:20px">
    <h2 style="font-size:18px;font-weight:700;margin-bottom:12px;display:flex;align-items:center;gap:8px;">
      <span>📋</span> 系统日志
      <button style="margin-left:auto;padding:4px 12px;height:28px;border-radius:6px;border:1px solid #d9d9d9;background:#fff;font-size:12px;cursor:pointer;color:#333" @click="loadLogs">{{ logsLoading ? '加载中...' : '刷新' }}</button>
    </h2>
    <div v-if="logs.length === 0 && !logsLoading" style="text-align:center;padding:32px;color:#999;font-size:13px">暂无日志</div>
    <div v-for="log in logs" :key="log.path" style="margin-bottom:12px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
      <div style="padding:8px 12px;background:#f8fafc;font-size:12px;font-weight:600;color:#475569;border-bottom:1px solid #e5e7eb;display:flex;justify-content:space-between">
        <span>📄 {{ log.file }}</span>
        <span style="font-weight:400;color:#94a3b8;font-size:11px">{{ log.path }}</span>
      </div>
      <pre style="margin:0;padding:12px;font-size:11px;line-height:1.6;max-height:400px;overflow:auto;background:#1e293b;color:#e2e8f0;font-family:SF Mono,Menlo,Monaco,Courier New,monospace;border-radius:0">{{ log.lines }}</pre>
    </div>
  </div>
</div>
</template>

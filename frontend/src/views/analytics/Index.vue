<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
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
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
      <h2 style="font-size:18px;font-weight:700">📋 系统日志</h2>
      <div style="display:flex;gap:8px;align-items:center">
        <select v-model="logLevel" style="padding:3px 8px;height:28px;border-radius:6px;border:1px solid #d9d9d9;font-size:12px;background:#fff;outline:none">
          <option value="">全部级别</option>
          <option value="ERROR">ERROR</option>
          <option value="WARNING">WARNING</option>
          <option value="INFO">INFO</option>
          <option value="DEBUG">DEBUG</option>
        </select>
        <button style="padding:4px 12px;height:28px;border-radius:6px;border:1px solid #d9d9d9;background:#fff;font-size:12px;cursor:pointer;color:#333" @click="loadLogs">{{ logsLoading ? '加载中...' : '刷新' }}</button>
      </div>
    </div>
    <div v-if="filteredLogs.length === 0 && !logsLoading" style="text-align:center;padding:40px;color:#999;font-size:13px">暂无日志</div>
    <div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden">
      <table style="width:100%;border-collapse:collapse;font-size:12px">
        <thead>
          <tr style="background:#f8fafc;border-bottom:1px solid #e5e7eb">
            <th style="padding:8px 10px;text-align:left;font-weight:600;color:#64748b;width:180px">时间</th>
            <th style="padding:8px 10px;text-align:left;font-weight:600;color:#64748b;width:80px">级别</th>
            <th style="padding:8px 10px;text-align:left;font-weight:600;color:#64748b">事件</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, idx) in filteredLogs.slice(0, 200)" :key="idx"
            style="border-bottom:1px solid #f1f5f9;transition:background 0.1s"
            :style="{background: entry.level === 'ERROR' ? '#fef2f2' : entry.level === 'WARNING' ? '#fffbeb' : entry.level === 'DEBUG' ? '#f8fafc' : ''}"
            @mouseenter="$event.currentTarget.style.background = entry.level === 'ERROR' ? '#fee2e2' : '#f8fafc'"
            @mouseleave="$event.currentTarget.style.background = entry.level === 'ERROR' ? '#fef2f2' : entry.level === 'WARNING' ? '#fffbeb' : ''">
            <td style="padding:6px 10px;font-family:SF Mono,Menlo,monospace;color:#64748b;white-space:nowrap">{{ entry.time || '-' }}</td>
            <td style="padding:6px 10px">
              <span :style="{
                display:'inline-block',padding:'1px 8px',borderRadius:'4px',fontSize:'11px',fontWeight:600,
                color: entry.level === 'ERROR' ? '#dc2626' : entry.level === 'WARNING' ? '#d97706' : entry.level === 'INFO' ? '#2563eb' : '#78716c',
                background: entry.level === 'ERROR' ? '#fef2f2' : entry.level === 'WARNING' ? '#fffbeb' : entry.level === 'INFO' ? '#eff6ff' : '#f5f5f4'
              }">{{ entry.level }}</span>
            </td>
            <td style="padding:6px 10px;color:#1e293b;line-height:1.5;word-break:break-all">{{ entry.message || entry.raw }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="filteredLogs.length > 200" style="text-align:center;padding:12px;color:#999;font-size:12px">显示前 200 条，共 {{ filteredLogs.length }} 条</div>
  </div>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, MousePointerClick, Clock, ChevronLeft, ChevronRight } from '@lucide/vue'
import { searchApi } from '../../api'

const data = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const r = await searchApi.logs({ skip: (page.value - 1) * pageSize.value, limit: pageSize.value })
    data.value = r.items
    total.value = r.total
  } catch {}
  finally { loading.value = false }
}
onMounted(load)

function pageChange(p: number) { page.value = p; load() }
</script>

<template>
  <div>
    <div class="dash-card" style="padding:0;overflow:hidden">
      <div style="padding:16px 20px 12px;border-bottom:1px solid #F1F5F9;display:flex;align-items:center;justify-content:space-between">
        <div style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;color:#0F172A">
          <Search :size="16" stroke-width="1.5" color="#3B82F6" />
          <span>搜索日志</span>
        </div>
        <span style="font-size:12px;color:#64748B">共 {{ total }} 条记录</span>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
          <tr style="background:#F8FAFC;border-bottom:1px solid #E2E8F0">
            <th style="padding:10px 16px;text-align:left;font-weight:600;color:#64748B;width:35%">查询内容</th>
            <th style="padding:10px 16px;text-align:left;font-weight:600;color:#64748B;width:70px">类型</th>
            <th style="padding:10px 16px;text-align:left;font-weight:600;color:#64748B;width:60px">结果</th>
            <th style="padding:10px 16px;text-align:left;font-weight:600;color:#64748B;width:70px">延迟</th>
            <th style="padding:10px 16px;text-align:left;font-weight:600;color:#64748B;width:60px">命中</th>
            <th style="padding:10px 16px;text-align:left;font-weight:600;color:#64748B;width:60px">来源</th>
            <th style="padding:10px 16px;text-align:left;font-weight:600;color:#64748B;width:140px">时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data" :key="row.id" style="border-bottom:1px solid #F1F5F9;transition:background 0.1s" @mouseenter="$event.currentTarget.style.background = '#F8FAFC'" @mouseleave="$event.currentTarget.style.background = ''">
            <td style="padding:10px 16px;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#0F172A">{{ row.query }}</td>
            <td style="padding:10px 16px">
              <span style="display:inline-block;padding:1px 8px;border-radius:4px;font-size:11px;font-weight:500;background:#F0F9FF;color:#0284C7">{{ row.search_type }}</span>
            </td>
            <td style="padding:10px 16px;color:#0F172A">{{ row.results_count }}</td>
            <td style="padding:10px 16px;color:#64748B">{{ row.latency_ms?.toFixed(0) }}ms</td>
            <td style="padding:10px 16px">
              <span :style="{
                display:'inline-block',padding:'1px 8px',borderRadius:'4px',fontSize:'11px',fontWeight:600,
                background: row.hit ? '#ECFDF5' : '#FEF2F2',
                color: row.hit ? '#059669' : '#DC2626'
              }">{{ row.hit ? '是' : '否' }}</span>
            </td>
            <td style="padding:10px 16px;color:#64748B;font-size:12px">{{ row.source }}</td>
            <td style="padding:10px 16px;color:#94A3B8;font-size:12px;white-space:nowrap">{{ row.created_at ? new Date(row.created_at).toLocaleString() : '' }}</td>
          </tr>
          <tr v-if="data.length === 0">
            <td colspan="7" style="text-align:center;color:#94A3B8;padding:48px 16px;font-size:14px">
              <Search :size="32" stroke-width="1" color="#E2E8F0" style="display:block;margin:0 auto 12px" />
              暂无搜索日志
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!-- Pagination -->
    <div v-if="total > pageSize" style="display:flex;justify-content:center;align-items:center;gap:12px;margin-top:16px">
      <button style="display:flex;align-items:center;gap:4px;padding:0 12px;height:30px;border-radius:8px;border:1px solid #E2E8F0;background:#fff;font-size:12px;cursor:pointer;color:#0F172A;transition:all 0.12s" :disabled="page <= 1" :style="page <= 1 ? 'opacity:0.4;cursor:not-allowed' : ''" @click="pageChange(page-1)">
        <ChevronLeft :size="14" stroke-width="1.5" />
        <span>上一页</span>
      </button>
      <span style="font-size:12px;color:#64748B">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button style="display:flex;align-items:center;gap:4px;padding:0 12px;height:30px;border-radius:8px;border:1px solid #E2E8F0;background:#fff;font-size:12px;cursor:pointer;color:#0F172A;transition:all 0.12s" :disabled="page >= Math.ceil(total / pageSize)" :style="page >= Math.ceil(total / pageSize) ? 'opacity:0.4;cursor:not-allowed' : ''" @click="pageChange(page+1)">
        <span>下一页</span>
        <ChevronRight :size="14" stroke-width="1.5" />
      </button>
    </div>
  </div>
</template>

<style scoped>
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
</style>
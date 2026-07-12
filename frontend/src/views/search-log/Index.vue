<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search } from '@lucide/vue'
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
    <div style="margin-bottom:16px;font-size:13px;color:var(--apple-text-secondary)">
      共 {{ total }} 条搜索记录
    </div>
    <div class="apple-card" style="padding:0;overflow:hidden">
      <table class="apple-table">
        <thead>
          <tr>
            <th style="width:40%">查询内容</th>
            <th style="width:80px">类型</th>
            <th style="width:60px">结果</th>
            <th style="width:70px">延迟</th>
            <th style="width:50px">命中</th>
            <th style="width:60px">来源</th>
            <th style="width:140px">时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data" :key="row.id">
            <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px">{{ row.query }}</td>
            <td><span class="apple-tag">{{ row.search_type }}</span></td>
            <td>{{ row.results_count }}</td>
            <td>{{ row.latency_ms?.toFixed(0) }}ms</td>
            <td>
              <span :class="['apple-tag', row.hit ? 'hit-yes' : 'hit-no']"
                    :style="row.hit ? 'background:#e8f5e9;color:#1a7d36' : 'background:#fff0f0;color:#d32f2f'">
                {{ row.hit ? '是' : '否' }}
              </span>
            </td>
            <td style="font-size:12px;color:var(--apple-text-secondary)">{{ row.source }}</td>
            <td style="font-size:12px;color:var(--apple-text-tertiary)">{{ row.created_at ? new Date(row.created_at).toLocaleString() : '' }}</td>
          </tr>
          <tr v-if="data.length === 0">
            <td colspan="7" style="text-align:center;color:var(--apple-text-tertiary);padding:32px;font-size:14px">暂无搜索日志</td>
          </tr>
        </tbody>
      </table>
    </div>
    <!-- Pagination -->
    <div v-if="total > pageSize" style="display:flex;justify-content:center;align-items:center;gap:8px;margin-top:16px">
      <button class="apple-btn-outline" style="padding:0 10px;height:28px;font-size:11px" @click="pageChange(page-1)" :disabled="page<=1">上一页</button>
      <span style="font-size:12px;color:var(--apple-text-secondary)">{{ page }} / {{ Math.ceil(total/pageSize) }}</span>
      <button class="apple-btn-outline" style="padding:0 10px;height:28px;font-size:11px" @click="pageChange(page+1)" :disabled="page>=Math.ceil(total/pageSize)">下一页</button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { knowledgeApi, tagApi } from '../../api'
import { Plus, Search, Eye, Edit3, Trash2, X, Tag, FileText, Clock } from '@lucide/vue'

const router = useRouter()
const data = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const showModal = ref(false)
const editing = ref<any>({ title: '', content: '', summary: '', tags: [] })
const isEdit = ref(false)
const tags = ref<any[]>([])
const loading = ref(false)
const deleting = ref<number | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await knowledgeApi.list({ skip: (page.value - 1) * pageSize.value, limit: pageSize.value, search: search.value || undefined })
    data.value = res.items; total.value = res.total
  } catch {}
  loading.value = false
}

async function loadTags() { try { const r = await tagApi.list(); tags.value = r.items } catch {} }
onMounted(() => { load(); loadTags() })

function editRow(row: any) { isEdit.value = true; editing.value = { ...row, tags: row.tags || [] }; showModal.value = true }

async function deleteRow(id: number) {
  deleting.value = id
  try { await knowledgeApi.delete(id); load() } catch {}
  finally { deleting.value = null }
}

async function save() {
  try {
    if (isEdit.value) await knowledgeApi.update(editing.value.id, editing.value)
    else await knowledgeApi.create(editing.value)
    showModal.value = false; load()
  } catch {}
}

function newDoc() { isEdit.value = false; editing.value = { title: '', content: '', summary: '', tags: [] }; showModal.value = true }

function formatDate(ts: string) {
  if (!ts) return '-'
  const d = new Date(ts)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const totalPages = () => Math.ceil(total.value / pageSize.value)
</script>

<template>
  <div class="knowledge-page">
    <!-- Toolbar -->
    <div class="kb-toolbar">
      <div class="kb-search">
        <Search :size="14" class="kb-search-icon" stroke-width="1.5" />
        <input v-model="search" class="kb-search-input" placeholder="搜索知识..." @keyup.enter="load" />
      </div>
      <button class="kb-btn kb-btn-primary" @click="newDoc">
        <Plus :size="15" stroke-width="1.5" /> 新建
      </button>
    </div>

    <!-- Stats bar -->
    <div class="kb-stats">
      <FileText :size="13" stroke-width="1.5" />
      <span>{{ total }} 条知识</span>
      <span class="kb-stat-divider">|</span>
      <Clock :size="13" stroke-width="1.5" />
      <span>{{ data.filter(d => d.updated_at).length }} 已更新</span>
    </div>

    <!-- Table area (flex-grow to push pagination down) -->
    <div class="kb-table-area">
      <div class="kb-table-wrap">
        <table class="kb-table" v-if="!loading || data.length > 0">
          <thead>
            <tr>
              <th class="col-idx">#</th>
              <th class="col-title">标题</th>
              <th class="col-source">来源</th>
              <th class="col-chunks">片段</th>
              <th class="col-tags">标签</th>
              <th class="col-time">更新时间</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, ri) in data" :key="row.id" class="kb-row">
              <td class="col-idx"><span class="row-num">{{ (page - 1) * pageSize + ri + 1 }}</span></td>
              <td class="col-title">
                <span class="kb-title" @click="router.push('/knowledge/' + row.id)">{{ row.title || '(无标题)' }}</span>
              </td>
              <td class="col-source"><span class="kb-source">{{ row.source || '-' }}</span></td>
              <td class="col-chunks"><span class="kb-badge">{{ row.chunk_count || 0 }}</span></td>
              <td class="col-tags">
                <span v-if="row.tags?.length" class="kb-tag" v-for="t in row.tags" :key="t">{{ t }}</span>
                <span v-else class="no-tags">-</span>
              </td>
              <td class="col-time"><span class="kb-time">{{ formatDate(row.updated_at) }}</span></td>
              <td class="col-actions">
                <div class="row-actions">
                  <button class="row-btn view" title="查看" @click="router.push('/knowledge/' + row.id)"><Eye :size="13" stroke-width="1.5" /></button>
                  <button class="row-btn edit" title="编辑" @click="editRow(row)"><Edit3 :size="13" stroke-width="1.5" /></button>
                  <button class="row-btn delete" title="删除" :disabled="deleting === row.id" @click="deleteRow(row.id)">
                    <Trash2 :size="13" stroke-width="1.5" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="data.length === 0">
              <td colspan="7" class="empty-row">
                <div class="empty-state">
                  <FileText :size="36" stroke-width="1" style="color:#e8e8ed" />
                  <div class="empty-title">暂无知识</div>
                  <div class="empty-desc">点击"新建"按钮添加第一条知识</div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <!-- Loading skeleton -->
        <div v-if="loading && data.length === 0" class="loading-skel">
          <div v-for="i in 5" :key="i" class="skel-row">
            <div class="skel-cell" style="width:30px"></div>
            <div class="skel-cell" style="width:200px"></div>
            <div class="skel-cell" style="width:60px"></div>
            <div class="skel-cell" style="width:40px"></div>
            <div class="skel-cell" style="width:120px"></div>
            <div class="skel-cell" style="width:120px"></div>
            <div class="skel-cell" style="width:80px"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination (fixed at bottom) -->
    <div v-if="total > pageSize" class="kb-pagination">
      <button class="page-btn" :disabled="page <= 1" @click="page--; load()">上一页</button>
      <div class="page-info">
        第 {{ page }} / {{ totalPages() }} 页
        <span class="page-divider">|</span>
        {{ total }} 条
      </div>
      <button class="page-btn" :disabled="page >= totalPages()" @click="page++; load()">下一页</button>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <span class="modal-title">{{ isEdit ? '编辑知识' : '新建知识' }}</span>
          <button class="modal-close" @click="showModal = false"><X :size="16" stroke-width="1.5" /></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>标题</label>
            <input v-model="editing.title" class="apple-input" placeholder="输入标题" />
          </div>
          <div class="form-group">
            <label>摘要</label>
            <textarea v-model="editing.summary" class="apple-textarea" rows="2" placeholder="输入摘要（可选）"></textarea>
          </div>
          <div class="form-group">
            <label>内容</label>
            <textarea v-model="editing.content" class="apple-textarea" rows="8" placeholder="输入内容"></textarea>
          </div>
          <div class="form-group">
            <label>标签</label>
            <div class="tag-select">
              <span v-for="t in tags" :key="t.name"
                :class="['tag-option', { active: editing.tags?.includes(t.name) }]"
                @click="editing.tags = editing.tags?.includes(t.name) ? editing.tags.filter((s:string) => s !== t.name) : [...(editing.tags||[]), t.name]">
                <Tag :size="11" stroke-width="1.5" /> {{ t.name }}
              </span>
              <span v-if="!tags.length" style="color:#aeaeb2;font-size:12px">暂无可用标签</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="kb-btn" @click="showModal = false">取消</button>
          <button class="kb-btn kb-btn-primary" @click="save">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.knowledge-page { display:flex; flex-direction:column; height:100%; font-family:-apple-system,BlinkMacSystemFont,SF Pro Text,Helvetica Neue,sans-serif; color:#1d1d1f; }
.kb-toolbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; gap:12px; flex-shrink:0; }
.kb-search { position:relative; flex:1; max-width:320px; }
.kb-search-icon { position:absolute; left:10px; top:50%; transform:translateY(-50%); color:#aeaeb2; pointer-events:none; }
.kb-search-input { width:100%; height:34px; padding-left:32px; border:1px solid #e5e5ea; border-radius:8px; font-size:13px; color:#1d1d1f; background:#fff; outline:none; }
.kb-search-input:focus { border-color:#0071e3; }
.kb-search-input::placeholder { color:#aeaeb2; }
.kb-btn { display:inline-flex; align-items:center; gap:6px; padding:0 16px; height:34px; border-radius:8px; font-size:13px; cursor:pointer; border:1px solid #e5e5ea; background:#fff; color:#1d1d1f; }
.kb-btn:hover { background:#f5f5f7; border-color:#d1d1d6; }
.kb-btn-primary { background:#0071e3; color:#fff; border-color:#0071e3; }
.kb-btn-primary:hover { background:#0077ed; }
.kb-stats { display:flex; align-items:center; gap:6px; font-size:12px; color:#8e8e93; margin-bottom:10px; flex-shrink:0; }
.kb-stat-divider { color:#d1d1d6; }

/* Table area - flex-grow to push pagination to bottom */
.kb-table-area { flex:1; min-height:0; display:flex; flex-direction:column; }
.kb-table-wrap { flex:1; border:1px solid #f0f0f0; border-radius:10px; overflow:auto; background:#fff; }
.kb-table { width:100%; border-collapse:collapse; font-size:12px; }
.kb-table thead th { position:sticky; top:0; z-index:1; background:#fafafc; padding:10px 14px; text-align:left; color:#6e6e73; border-bottom:1px solid #e8e8ed; white-space:nowrap; }
.col-idx { width:44px; text-align:center; }
.col-title { min-width:180px; }
.col-source { width:70px; }
.col-chunks { width:50px; text-align:center; }
.col-tags { min-width:100px; }
.col-time { width:140px; }
.col-actions { width:100px; text-align:center; }
.kb-row td { padding:8px 14px; border-bottom:1px solid #f0f0f2; vertical-align:middle; }
.kb-row:hover td { background:#fafafc; }
.kb-row:last-child td { border-bottom:none; }
.row-num { color:#aeaeb2; font-size:11px; }
.kb-title { color:#1d1d1f; cursor:pointer; }
.kb-title:hover { color:#0071e3; }
.kb-source { color:#8e8e93; font-size:11px; }
.kb-badge { display:inline-block; padding:1px 7px; border-radius:4px; background:#f0f0f5; color:#6e6e73; font-size:11px; }
.kb-tag { display:inline-block; padding:1px 6px; margin:1px 2px; border-radius:4px; background:#0071e310; color:#0071e3; font-size:10px; }
.no-tags { color:#d1d1d6; }
.kb-time { color:#8e8e93; font-size:11px; }
.row-actions { display:flex; gap:4px; justify-content:center; }
.row-btn { width:26px; height:26px; border-radius:6px; border:none; background:transparent; cursor:pointer; display:flex; align-items:center; justify-content:center; color:#aeaeb2; }
.row-btn:hover { background:#f0f0f5; }
.row-btn.view:hover { color:#0071e3; background:#0071e310; }
.row-btn.edit:hover { color:#ff9f0a; background:#ff9f0a10; }
.row-btn.delete:hover { color:#ff3b30; background:#ff3b3010; }
.row-btn:disabled { opacity:0.3; cursor:default; }
.empty-row td { padding:60px 14px; }
.empty-state { display:flex; flex-direction:column; align-items:center; gap:8px; color:#aeaeb2; }
.empty-title { font-size:15px; color:#8e8e93; }
.empty-desc { font-size:12px; }
.loading-skel { padding:14px; }
.skel-row { display:flex; gap:10px; margin-bottom:8px; }
.skel-cell { height:16px; border-radius:4px; background:linear-gradient(90deg,#f0f0f2 25%,#e8e8ed 50%,#f0f0f2 75%);background-size:200% 100%;animation:shimmer 1.2s infinite; }
@keyframes shimmer { 0%{background-position:200% 0}100%{background-position:-200% 0} }

/* Pagination - fixed at bottom */
.kb-pagination { display:flex; align-items:center; justify-content:center; gap:12px; padding:10px 0; flex-shrink:0; }
.page-btn { padding:4px 14px; height:28px; border-radius:6px; border:1px solid #e5e5ea; background:#fff; color:#6e6e73; font-size:12px; cursor:pointer; }
.page-btn:hover:not(:disabled) { background:#f5f5f7; color:#1d1d1f; }
.page-btn:disabled { opacity:0.4; cursor:default; }
.page-info { font-size:12px; color:#6e6e73; display:flex; align-items:center; gap:6px; }
.page-divider { color:#d1d1d6; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; z-index:1000; backdrop-filter:blur(4px); }
.modal-card { width:640px; max-height:85vh; background:#fff; border-radius:14px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.15); }
.modal-header { display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid #f0f0f0; }
.modal-title { font-size:15px; color:#1d1d1f; }
.modal-close { width:28px; height:28px; border-radius:8px; border:none; background:transparent; color:#aeaeb2; cursor:pointer; display:flex; align-items:center; justify-content:center; }
.modal-close:hover { background:#f0f0f5; color:#1d1d1f; }
.modal-body { padding:20px; overflow-y:auto; max-height:calc(85vh - 110px); }
.modal-footer { display:flex; justify-content:flex-end; gap:8px; padding:14px 20px; border-top:1px solid #f0f0f0; }
.form-group { margin-bottom:16px; }
.form-group label { display:block; font-size:12px; color:#6e6e73; margin-bottom:6px; }
.apple-input { width:100%; padding:8px 12px; border:1px solid #e5e5ea; border-radius:8px; font-size:13px; color:#1d1d1f; outline:none; background:#fff; box-sizing:border-box; }
.apple-input:focus { border-color:#0071e3; }
.apple-textarea { width:100%; padding:8px 12px; border:1px solid #e5e5ea; border-radius:8px; font-size:13px; color:#1d1d1f; outline:none; resize:vertical; font-family:inherit; line-height:1.5; background:#fff; box-sizing:border-box; }
.apple-textarea:focus { border-color:#0071e3; }
.tag-select { display:flex; flex-wrap:wrap; gap:6px; }
.tag-option { display:inline-flex; align-items:center; gap:4px; padding:3px 10px; border-radius:6px; border:1px solid #e5e5ea; font-size:12px; color:#6e6e73; cursor:pointer; }
.tag-option:hover { border-color:#0071e3; color:#0071e3; }
.tag-option.active { background:#0071e310; border-color:#0071e3; color:#0071e3; }
</style>
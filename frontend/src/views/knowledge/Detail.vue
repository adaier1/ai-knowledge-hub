<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { knowledgeApi } from '../../api'
import { Edit3, RotateCcw, X } from '@lucide/vue'

const route = useRoute()
const kn = ref<any>({})
const chunks = ref<any[]>([])
const related = ref<any[]>([])
const showEdit = ref(false)
const editForm = ref<any>({})
const loading = ref(true)

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    kn.value = await knowledgeApi.get(id)
    editForm.value = { ...kn.value, tags: kn.value.tags || [] }
  } catch {}
  try { chunks.value = (await knowledgeApi.getChunks(id)).items || [] } catch {}
  try { related.value = (await knowledgeApi.getRelated(id)).items || [] } catch {}
  loading.value = false
})

async function save() {
  try {
    await knowledgeApi.update(kn.value.id, editForm.value)
    kn.value = await knowledgeApi.get(kn.value.id)
    showEdit.value = false
  } catch {}
}

async function rebuildEmbedding() {
  try { await knowledgeApi.embed(kn.value.id) } catch {}
}
</script>

<template>
  <div v-if="!loading && kn.id" class="detail-page">
    <!-- Header -->
    <div class="detail-header">
      <div class="detail-title-row">
        <h1 class="detail-title">{{ kn.title }}</h1>
        <div class="detail-actions">
          <button class="kb-btn" @click="showEdit = true"><Edit3 :size="14" stroke-width="1.5" /> 编辑</button>
          <button class="kb-btn" @click="rebuildEmbedding"><RotateCcw :size="14" stroke-width="1.5" /> 重建向量</button>
        </div>
      </div>
    </div>

    <div class="detail-grid">
      <!-- Left column -->
      <div class="detail-main">
        <div class="info-card">
          <div class="info-card-title">内容</div>
          <div class="info-card-body" style="white-space:pre-wrap;line-height:1.7">{{ kn.content }}</div>
        </div>
        <div v-if="kn.summary" class="info-card">
          <div class="info-card-title">摘要</div>
          <div class="info-card-body">{{ kn.summary }}</div>
        </div>
        <div class="info-card">
          <div class="info-card-title">片段 ({{ chunks.length }})</div>
          <div class="chunk-list">
            <div v-for="(c, i) in chunks" :key="i" class="chunk-item">
              <span class="chunk-idx">#{{ c.chunk_index || i + 1 }}</span>
              <span class="chunk-text">{{ c.content }}</span>
              <span v-if="c.token_count" class="chunk-tokens">{{ c.token_count }} tokens</span>
            </div>
            <div v-if="!chunks.length" style="color:#aeaeb2;font-size:12px;padding:10px 0">无片段</div>
          </div>
        </div>
      </div>

      <!-- Right column -->
      <div class="detail-side">
        <div class="info-card">
          <div class="info-card-title">信息</div>
          <div class="info-card-body">
            <div class="meta-row"><span class="meta-label">来源</span><span>{{ kn.source || '-' }}</span></div>
            <div class="meta-row"><span class="meta-label">文件类型</span><span>{{ kn.file_type || '-' }}</span></div>
            <div class="meta-row"><span class="meta-label">Token 数</span><span>{{ kn.token_count || 0 }}</span></div>
            <div class="meta-row"><span class="meta-label">片段数</span><span>{{ kn.chunk_count || 0 }}</span></div>
            <div class="meta-row"><span class="meta-label">创建时间</span><span>{{ new Date(kn.created_at).toLocaleString() }}</span></div>
            <div class="meta-row"><span class="meta-label">更新时间</span><span>{{ new Date(kn.updated_at).toLocaleString() }}</span></div>
          </div>
        </div>
        <div class="info-card">
          <div class="info-card-title">标签</div>
          <div class="info-card-body">
            <span v-if="kn.tags?.length" class="kb-tag" v-for="t in kn.tags" :key="t">{{ t }}</span>
            <span v-else style="color:#aeaeb2;font-size:12px">无标签</span>
          </div>
        </div>
        <div class="info-card">
          <div class="info-card-title">相关知识</div>
          <div class="info-card-body">
            <div v-for="r in related" :key="r.id" class="related-item" @click="$router.push('/knowledge/' + r.id)">{{ r.title }}</div>
            <div v-if="!related.length" style="color:#aeaeb2;font-size:12px">暂无相关知识</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEdit" class="modal-overlay" @click.self="showEdit = false">
      <div class="modal-card">
        <div class="modal-header">
          <span class="modal-title">编辑知识</span>
          <button class="modal-close" @click="showEdit = false"><X :size="16" stroke-width="1.5" /></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label>标题</label><input v-model="editForm.title" class="apple-input" /></div>
          <div class="form-group"><label>摘要</label><textarea v-model="editForm.summary" class="apple-input" rows="2"></textarea></div>
          <div class="form-group"><label>内容</label><textarea v-model="editForm.content" class="apple-input" rows="10"></textarea></div>
        </div>
        <div class="modal-footer">
          <button class="kb-btn" @click="showEdit = false">取消</button>
          <button class="kb-btn kb-btn-primary" @click="save">保存</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Loading state -->
  <div v-else-if="loading" class="loading-state">
    <div class="loading-spinner"></div>
    <div style="color:#aeaeb2;font-size:13px;margin-top:12px">加载中...</div>
  </div>
</template>

<style scoped>
.detail-page { font-family:-apple-system,BlinkMacSystemFont,SF Pro Text,Helvetica Neue,sans-serif; color:#1d1d1f; }
.detail-header { margin-bottom:16px; }
.detail-title-row { display:flex; justify-content:space-between; align-items:center; }
.detail-title { font-size:18px; font-weight:600; margin:0; }
.detail-actions { display:flex; gap:8px; }
.detail-grid { display:grid; grid-template-columns:2fr 1fr; gap:16px; align-items:start; }
.detail-main { display:flex; flex-direction:column; gap:12px; }
.detail-side { display:flex; flex-direction:column; gap:12px; }

.info-card { border:1px solid #f0f0f0; border-radius:10px; background:#fff; overflow:hidden; }
.info-card-title { padding:10px 14px; font-size:12px; font-weight:600; color:#6e6e73; background:#fafafc; border-bottom:1px solid #f0f0f0; }
.info-card-body { padding:14px; font-size:13px; line-height:1.6; }
.meta-row { display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #f5f5f7; font-size:12px; }
.meta-row:last-child { border-bottom:none; }
.meta-label { color:#aeaeb2; }
.chunk-list { max-height:400px; overflow-y:auto; }
.chunk-item { display:flex; align-items:flex-start; gap:10px; padding:8px 0; border-bottom:1px solid #f5f5f7; font-size:12px; }
.chunk-item:last-child { border-bottom:none; }
.chunk-idx { color:#aeaeb2; font-size:11px; white-space:nowrap; min-width:24px; }
.chunk-text { flex:1; color:#636366; overflow:hidden; text-overflow:ellipsis; }
.chunk-tokens { color:#aeaeb2; font-size:10px; white-space:nowrap; }
.related-item { padding:8px 0; border-bottom:1px solid #f5f5f7; font-size:12px; color:#0071e3; cursor:pointer; }
.related-item:hover { text-decoration:underline; }
.related-item:last-child { border-bottom:none; }

.kb-btn { display:inline-flex; align-items:center; gap:6px; padding:0 14px; height:32px; border-radius:8px; font-size:12px; cursor:pointer; border:1px solid #e5e5ea; background:#fff; color:#1d1d1f; }
.kb-btn:hover { background:#f5f5f7; border-color:#d1d1d6; }
.kb-btn-primary { background:#0071e3; color:#fff; border-color:#0071e3; }
.kb-btn-primary:hover { background:#0077ed; }
.kb-tag { display:inline-block; padding:2px 8px; margin:2px 3px; border-radius:5px; background:#0071e310; color:#0071e3; font-size:11px; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; z-index:1000; backdrop-filter:blur(4px); }
.modal-card { width:640px; max-height:85vh; background:#fff; border-radius:14px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.15); }
.modal-header { display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid #f0f0f0; }
.modal-title { font-size:15px; font-weight:600; color:#1d1d1f; }
.modal-close { width:28px; height:28px; border-radius:8px; border:none; background:transparent; color:#aeaeb2; cursor:pointer; display:flex; align-items:center; justify-content:center; }
.modal-close:hover { background:#f0f0f5; color:#1d1d1f; }
.modal-body { padding:20px; overflow-y:auto; max-height:calc(85vh - 110px); }
.modal-footer { display:flex; justify-content:flex-end; gap:8px; padding:14px 20px; border-top:1px solid #f0f0f0; }
.form-group { margin-bottom:16px; }
.form-group label { display:block; font-size:12px; font-weight:500; color:#6e6e73; margin-bottom:6px; }
.apple-input { width:100%; padding:8px 12px; border:1px solid #e5e5ea; border-radius:8px; font-size:13px; color:#1d1d1f; outline:none; font-family:inherit; resize:vertical; box-sizing:border-box; }
.apple-input:focus { border-color:#0071e3; }
.loading-state { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:60px 0; }
.loading-spinner { width:20px; height:20px; border:2px solid #e8e8ed; border-top-color:#0071e3; border-radius:50%; animation:spin .6s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
</style>
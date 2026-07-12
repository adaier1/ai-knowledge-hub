<script setup lang="ts">
import { ref, computed, onMounted, h } from "vue"
import { useMessage } from "naive-ui"
import api from "../../api"
import {
  Database, Table, Search, Play, RotateCw, Terminal, X,
  ChevronRight, FileJson, Columns, Hash, AlignLeft, Type, Clock, Server,
  Download, Upload
} from "@lucide/vue"

const message = useMessage()
const tables = ref([])
const selectedTable = ref("")
const tableData = ref([])
const tableColumns = ref([])
const tableTotal = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loading = ref(false)
const sidebarWidth = ref(260)
const sidebarCollapsed = ref(false)
const tableSearch = ref("")
const sqlQuery = ref("")
const sqlResult = ref(null)
const sqlLoading = ref(false)
const showSql = ref(false)
const resizing = ref(false)
const dbFiles = ref([])
const selectedDbFile = ref("knowledge.db")
const importingDb = ref(false)

const zh = {t1:"张表",t2:"条记录",t3:"查询",t4:"刷新",t5:"侧栏",t6:"搜索表...",t7:"无匹配表",t8:"暂无表",t9:"执行中...",t10:"执行",t11:"查询完成，返回",t12:"行",t13:"选择一个表开始浏览",t14:"从左侧列表中选择一个表查看数据",t15:"上一页",t16:"第",t17:"页",t18:"下一页",t19:"条",t20:"每页",t21:"已连接",t22:"加载失败: ",t23:"导出",t24:"导入"}

const filteredTables = computed(() => {
  if (!tableSearch.value) return tables.value
  const q = tableSearch.value.toLowerCase()
  return tables.value.filter((t) => t.name.toLowerCase().includes(q))
})

const totalRecords = computed(() =>
  tables.value.reduce((s, t) => s + (t.row_count || 0), 0)
)

const activeDbFile = computed(() => {
  return dbFiles.value.find(f => f.name === selectedDbFile.value)
})

function getTableColor(name) {
  const map = { knowledge:"#0071e3", tag:"#34c759", chunk:"#ff9f0a", entity:"#ff3b30", relation:"#af52de", setting:"#30b0c7", mcp:"#5856d6", search:"#30c79a", user:"#ff6b35" }
  for (const [k,v] of Object.entries(map)) { if (name.includes(k)) return v }
  return "#86868b"
}

async function loadDbFiles() {
  try {
    const r = await api.get("/database/files")
    dbFiles.value = r.data.files || []
    if (dbFiles.value.length > 0 && !dbFiles.value.find(f => f.name === selectedDbFile.value)) {
      selectedDbFile.value = dbFiles.value[0].name
    }
  } catch {}
}

async function loadTables() {
  try {
    const r = await api.get("/database/tables", { params: { db_file: selectedDbFile.value } })
    tables.value = (r.data.items || []).sort((a, b) => a.name.localeCompare(b.name))
  } catch { tables.value = [] }
}

async function loadTable() {
  if (!selectedTable.value) return; loading.value = true
  try {
    const r = await api.get("/database/tables/" + selectedTable.value, {
      params: { skip: (page.value - 1) * pageSize.value, limit: pageSize.value, db_file: selectedDbFile.value }
    })
    tableColumns.value = (r.data.columns || []).map((c) => {
      const isId = c === "id" || c.endsWith("_id")
      const isJson = ["metadata","tags","meta","json"].some(k => c.toLowerCase().includes(k))
      const isLong = ["content","body","description","text","summary"].includes(c)
      const isTime = ["created_at","updated_at","date","time"].some(k => c.toLowerCase().includes(k))
      return {
        title: c, key: c,
        width: isId ? 80 : isTime ? 180 : isJson ? 200 : isLong ? 300 : 150,
        ellipsis: { tooltip: true }, sortable: true,
        render: (row) => {
          const val = row[c]
          if (val === null || val === undefined) return h("span", { style: "color:#86868b;font-style:italic" }, "NULL")
          if (isJson && typeof val === "string") {
            try { const p = JSON.parse(val); const s = JSON.stringify(p); return h("span", { style: "color:#af52de;cursor:pointer", title: JSON.stringify(p, null, 2) }, s.slice(0, 60) + (s.length > 60 ? "..." : "")) }
            catch { return h("span", val) }
          }
          if (typeof val === "string" && val.length > 80) return h("span", { style: "cursor:pointer", title: val }, val.slice(0, 80) + "...")
          if (isTime && typeof val === "string") return h("span", { style: "color:#0071e3;font-size:12px" }, val)
          return h("span", String(val))
        }
      }
    })
    tableData.value = r.data.rows || []; tableTotal.value = r.data.total || 0
  } catch (e) { message.error(zh.t22 + (e.response?.data?.detail || e.message)); tableData.value = []; tableColumns.value = [] }
  finally { loading.value = false }
}

function selectTable(name) { selectedTable.value = name; page.value = 1; loadTable() }

async function onDbFileChange() {
  selectedTable.value = ""; tableData.value = []; tableColumns.value = []; page.value = 1
  await loadTables()
}

async function runSql() {
  if (!sqlQuery.value) return; sqlLoading.value = true
  try {
    const r = await api.post("/database/query", { sql: sqlQuery.value }, { params: { db_file: selectedDbFile.value } })
    sqlResult.value = r.data
  } catch (e) { sqlResult.value = { error: e.response?.data?.detail || e.message } }
  finally { sqlLoading.value = false }
}

function refresh() { if (selectedTable.value) loadTable(); loadTables() }
function formatJsonPreview(str) {
  try { const p = JSON.parse(str); const s = JSON.stringify(p); return s.length > 60 ? s.slice(0, 60) + "..." : s }
  catch { return str.length > 60 ? str.slice(0, 60) + "..." : str }
}
function startResize(e) {
  resizing.value = true; const sx = e.clientX, sw = sidebarWidth.value
  const move = (ev) => { sidebarWidth.value = Math.max(180, Math.min(500, sw + ev.clientX - sx)) }
  const up = () => { resizing.value = false; document.removeEventListener("mousemove", move); document.removeEventListener("mouseup", up) }
  document.addEventListener("mousemove", move); document.addEventListener("mouseup", up)
}

function exportDb() {
  if (!selectedDbFile.value) return
  const a = document.createElement("a")
  a.href = "/api/database/export?db_file=" + encodeURIComponent(selectedDbFile.value)
  a.download = selectedDbFile.value
  a.click()
  message.success("已导出: " + selectedDbFile.value)
}

function triggerImport() {
  const input = document.createElement("input")
  input.type = "file"; input.accept = ".db"
  input.onchange = async () => {
    const file = input.files?.[0]; if (!file) return
    importingDb.value = true
    try {
      const fd = new FormData(); fd.append("file", file)
      const r = await api.post("/database/import", fd)
      if (r.data.success) { message.success(r.data.message || "导入成功"); await loadDbFiles() }
    } catch (e) { message.error(zh.t22 + (e.response?.data?.detail || e.message)) }
    finally { importingDb.value = false }
  }
  input.click()
}

onMounted(async () => { await loadDbFiles(); await loadTables() })
</script>

<template>
  <div class="db-manager">
    <div class="db-toolbar">
      <div class="toolbar-left">
        <Database :size="18" stroke-width="1.5" style="color:#0071e3" />
        <select v-model="selectedDbFile" class="db-select" @change="onDbFileChange">
          <option v-for="f in dbFiles" :key="f.name" :value="f.name">{{ f.name }} {{ f.active ? '(当前)' : '' }}</option>
        </select>
        <span class="toolbar-badge">SQLite</span>
        <span v-if="activeDbFile" class="toolbar-size">{{ activeDbFile.size_mb }} MB</span>
      </div>
      <div class="toolbar-center">
        <span>{{ tables.length }} {{ zh.t1 }}</span>
        <span class="toolbar-divider">|</span>
        <span>{{ totalRecords.toLocaleString() }} {{ zh.t2 }}</span>
      </div>
      <div class="toolbar-right">
        <button class="tb-btn" @click="exportDb" :title="zh.t23">
          <Download :size="16" stroke-width="1.5" /><span>{{ zh.t23 }}</span>
        </button>
        <button class="tb-btn" @click="triggerImport" :title="zh.t24" :disabled="importingDb">
          <Upload :size="16" stroke-width="1.5" /><span>{{ importingDb ? "..." : zh.t24 }}</span>
        </button>
        <button class="tb-btn" :class="{ active: showSql }" @click="showSql = !showSql" title="SQL 查询">
          <Terminal :size="16" stroke-width="1.5" /><span>SQL</span>
        </button>
        <button class="tb-btn" @click="refresh" :title="zh.t4">
          <RotateCw :size="16" stroke-width="1.5" /><span>{{ zh.t4 }}</span>
        </button>
        <button class="tb-btn" @click="sidebarCollapsed = !sidebarCollapsed" :title="zh.t5">
          <Columns :size="16" stroke-width="1.5" />
        </button>
      </div>
    </div>

    <div class="db-body">
      <div class="db-sidebar" :style="{ width: sidebarCollapsed ? '0px' : sidebarWidth + 'px' }" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <Search :size="14" stroke-width="1.5" style="color:#86868b" />
          <input v-model="tableSearch" class="sidebar-search" :placeholder="zh.t6" />
        </div>
        <div class="sidebar-list">
          <div v-for="t in filteredTables" :key="t.name" class="sidebar-item" :class="{ active: selectedTable === t.name }" @click="selectTable(t.name)">
            <div class="item-icon" :style="{ background: getTableColor(t.name) + '15', color: getTableColor(t.name) }"><Table :size="14" stroke-width="1.5" /></div>
            <span class="item-name">{{ t.name }}</span>
            <span class="item-count">{{ t.row_count || 0 }}</span>
          </div>
          <div v-if="filteredTables.length === 0" class="sidebar-empty">{{ tableSearch ? zh.t7 : zh.t8 }}</div>
        </div>
      </div>
      <div v-if="!sidebarCollapsed" class="sidebar-resizer" @mousedown="startResize" :class="{ resizing }"></div>
      <div class="db-content">
        <div v-if="showSql" class="sql-panel">
          <div class="sql-header">
            <span><Terminal :size="14" stroke-width="1.5" style="color:#0071e3" /> SQL {{ zh.t3 }}</span>
            <button class="sql-close" @click="showSql = false"><X :size="14" stroke-width="1.5" /></button>
          </div>
          <div class="sql-editor"><textarea v-model="sqlQuery" class="sql-textarea" placeholder="SELECT * FROM knowledge LIMIT 50" spellcheck="false"></textarea></div>
          <div class="sql-actions">
            <button class="sql-run-btn" @click="runSql" :disabled="sqlLoading">
              <Play :size="14" stroke-width="1.5" /> {{ sqlLoading ? zh.t9 : zh.t10 }}
            </button>
          </div>
          <div v-if="sqlResult" class="sql-result">
            <div v-if="sqlResult.error" class="sql-error">{{ sqlResult.error }}</div>
            <div v-else><div class="sql-ok-header">{{ zh.t11 }} {{ (sqlResult.rows || []).length }} {{ zh.t12 }}</div><pre class="sql-output">{{ JSON.stringify(sqlResult, null, 2) }}</pre></div>
          </div>
        </div>
        <div v-if="selectedTable" class="table-header">
          <div class="table-title-row">
            <div style="display:flex;align-items:center;gap:8px">
              <Table :size="16" stroke-width="1.5" style="color:#0071e3" />
              <span class="table-name">{{ selectedTable }}</span>
              <span class="table-records">{{ tableTotal.toLocaleString() }} {{ zh.t2 }}</span>
              <span v-if="loading" class="loading-spinner"></span>
            </div>
          </div>
        </div>
        <div v-if="!selectedTable" class="db-empty">
          <Database :size="48" stroke-width="1" style="color:#e8e8ed" />
          <div class="empty-title">{{ zh.t13 }}</div>
          <div class="empty-desc">{{ zh.t14 }}</div>
        </div>
        <div v-if="loading && tableData.length === 0" class="loading-skeleton">
          <div v-for="i in 5" :key="i" class="skeleton-row"><div v-for="j in 6" :key="j" class="skeleton-cell"></div></div>
        </div>
        <div v-if="selectedTable && (!loading || tableData.length > 0)" class="data-grid-container">
          <table class="data-grid" v-if="tableColumns.length > 0">
            <thead><tr>
              <th class="row-num">#</th>
              <th v-for="col in tableColumns" :key="col.key" class="col-header" :style="{ width: col.width + 'px' }">
                <div class="col-header-inner">
                  <component :is="['id','_id'].some(k=>col.key===k) ? Hash : ['created_at','updated_at','date'].some(k=>col.key.includes(k)) ? Clock : ['content','body','description'].some(k=>col.key.includes(k)) ? AlignLeft : ['metadata','tags','json'].some(k=>col.key.includes(k)) ? FileJson : Type" :size="12" stroke-width="1.5" style="color:#86868b" />
                  <span>{{ col.title }}</span>
                </div>
              </th>
            </tr></thead>
            <tbody>
              <tr v-for="(row, ri) in tableData" :key="ri" class="data-row" :class="{ even: ri % 2 === 0 }">
                <td class="row-num">{{ (page - 1) * pageSize + ri + 1 }}</td>
                <td v-for="col in tableColumns" :key="col.key" class="data-cell">
                  <template v-if="row[col.key] === null || row[col.key] === undefined"><span class="null-value">NULL</span></template>
                  <template v-else-if="col.key === 'id' || col.key.endsWith('_id')"><span class="id-value">{{ row[col.key] }}</span></template>
                  <template v-else-if="['created_at','updated_at','date'].some(k=>col.key.includes(k))"><span class="time-value">{{ row[col.key] }}</span></template>
                  <template v-else-if="['metadata','tags','json'].some(k=>col.key.includes(k)) && typeof row[col.key] === 'string'"><span class="json-value" :title="row[col.key]">{{ formatJsonPreview(row[col.key]) }}</span></template>
                  <template v-else-if="['content','body','description','text'].includes(col.key) && typeof row[col.key] === 'string' && row[col.key].length > 80"><span class="text-value" :title="row[col.key]">{{ row[col.key].slice(0, 80) + '...' }}</span></template>
                  <template v-else><span>{{ String(row[col.key]) }}</span></template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="selectedTable && tableTotal > pageSize" class="pagination">
          <button class="page-btn" :disabled="page <= 1" @click="page--; loadTable()">{{ zh.t15 }}</button>
          <div class="page-info"><span>{{ zh.t16 }}{{ page }} / {{ Math.ceil(tableTotal / pageSize) }} {{ zh.t17 }}</span><span class="page-divider">|</span><span>{{ tableTotal.toLocaleString() }} {{ zh.t2 }}</span></div>
          <button class="page-btn" :disabled="page >= Math.ceil(tableTotal / pageSize)" @click="page++; loadTable()">{{ zh.t18 }}</button>
        </div>
        <div v-if="selectedTable" class="page-size-bar">
          <span>{{ zh.t20 }}</span>
          <select v-model.number="pageSize" class="page-size-select" @change="page=1;loadTable()">
            <option :value="25">25</option><option :value="50">50</option><option :value="100">100</option><option :value="200">200</option>
          </select>
          <span>{{ zh.t19 }}</span>
        </div>
      </div>
    </div>
    <div class="db-statusbar">
      <div class="status-left">
        <Server :size="13" stroke-width="1.5" style="color:#34c759" />
        <span>SQLite</span>
        <span class="status-divider">|</span>
        <span>{{ selectedDbFile }}</span>
        <span class="status-divider">|</span>
        <span>{{ tables.length }} {{ zh.t1 }}</span>
      </div>
      <div class="status-right">
        <span v-if="selectedTable">{{ selectedTable }}</span>
        <span class="status-divider" v-if="selectedTable">|</span>
        <span>{{ totalRecords.toLocaleString() }} {{ zh.t2 }}</span>
        <span class="status-divider">|</span>
        <span><span class="status-dot"></span> {{ zh.t21 }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.db-manager { display:flex;flex-direction:column;height:100%;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,SF Pro Text,Helvetica Neue,sans-serif;color:#1d1d1f;user-select:none; }
.db-toolbar { display:flex;align-items:center;justify-content:space-between;padding:6px 14px;background:#fafafc;border-bottom:1px solid #e8e8ed;height:44px;flex-shrink:0; }
.toolbar-left,.toolbar-center,.toolbar-right { display:flex;align-items:center;gap:10px; }
.toolbar-center { font-size:12px;color:#86868b; }
.toolbar-divider { color:#d1d1d6; }
.toolbar-badge { font-size:10px;background:#0071e315;color:#0071e3;padding:1px 7px;border-radius:4px;font-weight:500; }
.toolbar-size { font-size:11px;color:#86868b; }
.db-select { height:28px;border-radius:6px;border:1px solid #e8e8ed;background:#ffffff;padding:0 8px;font-size:12px;color:#1d1d1f;outline:none;cursor:pointer;min-width:140px; }
.db-select:focus { border-color:#0071e3; }
.tb-btn { display:flex;align-items:center;gap:5px;padding:4px 10px;height:28px;border-radius:6px;border:1px solid #e8e8ed;background:#ffffff;color:#6e6e73;font-size:12px;cursor:pointer;transition:all .15s; }
.tb-btn:hover { background:#f5f5f7;color:#1d1d1f;border-color:#d1d1d6; }
.tb-btn:disabled { opacity:.4;cursor:default; }
.tb-btn.active { background:#0071e3;color:#fff;border-color:#0071e3; }
.tb-btn.active:hover { background:#0077ed; }
.db-body { display:flex;flex:1;overflow:hidden; }
.db-sidebar { border-right:1px solid #e8e8ed;background:#fafafc;display:flex;flex-direction:column;overflow:hidden;transition:width .2s; }
.db-sidebar.collapsed { border-right:none; }
.sidebar-header { display:flex;align-items:center;gap:6px;padding:8px 10px;border-bottom:1px solid #e8e8ed; }
.sidebar-search { flex:1;border:none;background:transparent;outline:none;font-size:12px;color:#1d1d1f; }
.sidebar-search::placeholder { color:#86868b; }
.sidebar-list { flex:1;overflow-y:auto;padding:4px 6px; }
.sidebar-item { display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:6px;cursor:pointer;margin-bottom:1px;transition:background .1s; }
.sidebar-item:hover { background:#e8e8ed; }
.sidebar-item.active { background:#0071e315; }
.item-icon { width:24px;height:24px;border-radius:6px;display:flex;align-items:center;justify-content:center;flex-shrink:0; }
.item-name { flex:1;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#1d1d1f; }
.item-count { font-size:11px;color:#86868b;min-width:20px;text-align:right; }
.sidebar-empty { padding:14px;text-align:center;font-size:12px;color:#86868b; }
.sidebar-resizer { width:3px;cursor:col-resize;background:transparent;flex-shrink:0;position:relative; }
.sidebar-resizer:hover,.sidebar-resizer.resizing { background:#0071e3; }
.db-content { flex:1;display:flex;flex-direction:column;overflow:hidden;background:#ffffff; }
.sql-panel { border-bottom:1px solid #e8e8ed;background:#fafafc;flex-shrink:0; }
.sql-header { display:flex;align-items:center;justify-content:space-between;padding:6px 12px;font-size:12px;font-weight:500;border-bottom:1px solid #e8e8ed;color:#6e6e73; }
.sql-close { width:22px;height:22px;border-radius:4px;border:none;background:transparent;color:#86868b;cursor:pointer;display:flex;align-items:center;justify-content:center; }
.sql-close:hover { background:#e8e8ed;color:#1d1d1f; }
.sql-textarea { width:100%;height:90px;padding:10px 12px;background:#ffffff;color:#1d1d1f;border:none;outline:none;font-family:SF Mono,Consolas,monospace;font-size:13px;resize:vertical;line-height:1.5; }
.sql-textarea::placeholder { color:#86868b; }
.sql-actions { padding:6px 12px;border-top:1px solid #e8e8ed; }
.sql-run-btn { display:flex;align-items:center;gap:6px;padding:4px 14px;height:28px;border-radius:6px;border:none;background:#0071e3;color:#fff;font-size:12px;cursor:pointer; }
.sql-run-btn:disabled { opacity:.4;cursor:default; }
.sql-result { border-top:1px solid #e8e8ed;max-height:200px;overflow:auto; }
.sql-error { padding:10px 12px;color:#ff3b30;font-size:12px; }
.sql-ok-header { padding:6px 12px;font-size:12px;color:#86868b;border-bottom:1px solid #e8e8ed; }
.sql-output { padding:10px 12px;margin:0;font-size:12px;font-family:SF Mono,Consolas,monospace;color:#1d1d1f;white-space:pre-wrap;overflow-x:auto; }
.table-header { padding:8px 14px;border-bottom:1px solid #e8e8ed;background:#ffffff;flex-shrink:0; }
.table-title-row { display:flex;align-items:center;justify-content:space-between; }
.table-name { font-weight:600;font-size:14px; }
.table-records { font-size:12px;color:#86868b;margin-left:8px; }
.db-empty { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;color:#86868b; }
.empty-title { font-size:16px;color:#6e6e73;font-weight:500; }
.empty-desc { font-size:13px; }
.data-grid-container { flex:1;overflow:auto; }
.data-grid { width:100%;border-collapse:collapse;table-layout:auto;font-size:12px; }
.data-grid thead { position:sticky;top:0;z-index:5; }
.data-grid th { background:#fafafc;padding:6px 10px;text-align:left;font-weight:500;color:#6e6e73;border-bottom:1px solid #e8e8ed;white-space:nowrap; }
.col-header-inner { display:flex;align-items:center;gap:4px; }
.row-num { width:40px;text-align:center;color:#86868b;font-size:11px; }
.data-row td { padding:5px 10px;border-bottom:1px solid #f0f0f2;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#1d1d1f; }
.data-row:hover td { background:#f5f5f7; }
.data-row.even td { background:#fafafc; }
.data-row.even:hover td { background:#f5f5f7; }
.null-value { color:#86868b;font-style:italic;font-size:11px; }
.id-value { color:#0071e3;font-weight:500;font-family:SF Mono,monospace; }
.time-value { color:#0071e3;font-size:11px; }
.json-value { color:#af52de;cursor:pointer;font-size:11px; }
.text-value { color:#6e6e73; }
.loading-skeleton { padding:14px; }
.skeleton-row { display:flex;gap:8px;margin-bottom:6px; }
.skeleton-cell { height:16px;border-radius:4px;background:linear-gradient(90deg,#f0f0f2 25%,#e8e8ed 50%,#f0f0f2 75%);background-size:200% 100%;animation:shimmer 1.2s infinite;flex:1; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.loading-spinner { width:14px;height:14px;border:2px solid #e8e8ed;border-top-color:#0071e3;border-radius:50%;animation:spin .6s linear infinite;display:inline-block; }
@keyframes spin { to { transform:rotate(360deg); } }
.pagination { display:flex;align-items:center;justify-content:center;gap:12px;padding:8px 14px;border-top:1px solid #e8e8ed;background:#ffffff; }
.page-btn { padding:4px 12px;height:26px;border-radius:6px;border:1px solid #e8e8ed;background:#ffffff;color:#6e6e73;font-size:12px;cursor:pointer; }
.page-btn:hover:not(:disabled) { background:#f5f5f7;color:#1d1d1f; }
.page-btn:disabled { opacity:.4;cursor:default; }
.page-info { display:flex;align-items:center;gap:8px;font-size:12px;color:#6e6e73; }
.page-size-bar { display:flex;align-items:center;gap:6px;padding:4px 14px;border-top:1px solid #e8e8ed;background:#ffffff;justify-content:flex-end;font-size:12px;color:#86868b; }
.page-size-select { background:#ffffff;color:#1d1d1f;border:1px solid #e8e8ed;border-radius:4px;padding:2px 6px;font-size:12px;outline:none;cursor:pointer; }
.db-statusbar { display:flex;align-items:center;justify-content:space-between;height:28px;padding:0 14px;background:#fafafc;border-top:1px solid #e8e8ed;font-size:11px;color:#86868b;flex-shrink:0; }
.status-left,.status-right { display:flex;align-items:center;gap:6px; }
.status-dot { width:6px;height:6px;border-radius:50%;background:#34c759;display:inline-block; }
::-webkit-scrollbar { width:6px;height:6px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#e8e8ed;border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:#d1d1d6; }
</style>
<script setup lang="ts">
import { ref, onMounted, watch } from "vue"
import { useMessage } from "naive-ui"
import { settingsApi, webdavApi } from "../../api"
import api from "../../api"
import { Settings, Cpu, Search, Share2, Info, Cloud, Upload, Download, RefreshCw, Clock, Folder, FolderOpen, Eye, EyeOff } from '@lucide/vue'

const message = useMessage()
const embedding = ref({ provider: "openai", model: "text-embedding-3-small", dimension: 1536, batch_size: 10, timeout: 30, api_key: "", api_url: "" })
const retriever = ref({ top_k: 10 })
const graph = ref({ max_nodes: 200 })
const activeTab = ref("webdav")
const testing = ref(false)
const testingWebdav = ref(false)
const backingUp = ref(false)
const backingUpData = ref(false)
const restoringData = ref(false)
const showDetail = ref(false)
const testResult = ref<any>(null)
const importing = ref(false)
const dirBrowser = ref({ visible: false, loading: false, dirs: [], currentPath: '' })
const backupEnabled = ref(false)
const webdav = ref({ url: "", username: "", password: "", backup_path: "akh-backups", schedule_time: "", schedule_frequency: "daily", schedule_day: 1, retention_days: 30 })
const backupList = ref<any[]>([])

// Password toggle using direct DOM manipulation
const showPwd = ref(false)
function toggleShowPwd() {
  showPwd.value = !showPwd.value
}

const versions = ref<any[]>([])
const activeVersion = ref("v1")
const rebuilding = ref(false)
const rebuildResult = ref("")
const switching = ref(false)

const categories = [
  { key: "webdav", label: "备份", icon: Cloud },
  { key: "embedding", label: "向量模型", icon: Cpu },
  { key: "retriever", label: "检索", icon: Search },
  { key: "graph", label: "图谱", icon: Share2 },
  { key: "about", label: "关于", icon: Info },
]

const providerPresets: Record<string, { api_url: string; model: string; dimension: number }> = {
  openai: { api_url: "https://api.openai.com/v1", model: "text-embedding-3-small", dimension: 1536 },
  siliconflow: { api_url: "https://api.siliconflow.cn/v1", model: "BAAI/bge-large-zh-v1.5", dimension: 1024 },
  ollama: { api_url: "http://localhost:11434/v1", model: "nomic-embed-text", dimension: 768 },
  doubao: { api_url: "https://ark.cn-beijing.volces.com/api/v3", model: "doubao-embedding-vision-251215", dimension: 2048 },
}

watch(() => embedding.value.provider, (newVal) => {
  const preset = providerPresets[newVal]
  if (preset) {
    embedding.value.api_url = preset.api_url
    embedding.value.model = preset.model
    embedding.value.dimension = preset.dimension
  }
})

function extractEmbeddingConfig(r: any) {
  const cfg = r?.settings?.value || r?.settings || r
  if (typeof cfg === "object") {
    if (cfg.provider) embedding.value.provider = cfg.provider
    if (cfg.model) embedding.value.model = cfg.model
    if (cfg.dimension) embedding.value.dimension = cfg.dimension
    if (cfg.batch_size) embedding.value.batch_size = cfg.batch_size
    if (cfg.timeout) embedding.value.timeout = cfg.timeout
    if (cfg.api_key !== undefined) embedding.value.api_key = cfg.api_key
    if (cfg.api_url !== undefined) embedding.value.api_url = cfg.api_url
  }
}

async function loadSettings() {
  try {
    const r = await webdavApi.getConfig()
    Object.assign(webdav.value, r)
    if (webdav.value.password === '******') webdav.value.password = ''
    backupEnabled.value = r.schedule_enabled !== false && !!r.schedule_time
  } catch {}
  try {
    const r = await settingsApi.get("embedding")
    if (r) extractEmbeddingConfig(r)
  } catch {}
  await loadVersions()
  await refreshBackupList()
}
onMounted(loadSettings)

async function loadVersions() {
  try {
    const res = await api.get("/settings/embedding/rebuild/status")
    versions.value = res.data.versions || []
    activeVersion.value = res.data.active || "v1"
  } catch {}
}

async function saveWebdav() {
  try {
    await webdavApi.saveConfig({
      url: webdav.value.url, username: webdav.value.username, password: webdav.value.password,
      backup_path: webdav.value.backup_path, schedule_time: webdav.value.schedule_time,
      schedule_frequency: webdav.value.schedule_frequency, schedule_day: webdav.value.schedule_day,
      schedule_enabled: backupEnabled.value, retention_days: webdav.value.retention_days,
    })
    message.success("配置已保存")
  } catch { message.error("保存失败") }
}

async function testWebdav() {
  if (!webdav.value.url) { message.warning("请先填写 WebDAV 地址"); return }
  testingWebdav.value = true
  const timeout = setTimeout(() => {
    message.warning("连接超时（30秒），请检查地址和网络")
    testingWebdav.value = false
  }, 30000)
  try {
    const res = await webdavApi.test({ url: webdav.value.url, username: webdav.value.username, password: webdav.value.password, backup_path: webdav.value.backup_path })
    clearTimeout(timeout)
    if (res.success) message.success(res.message)
    else message.error(res.message)
  } catch (e: any) {
    clearTimeout(timeout)
    message.error("请求失败: " + (e.response?.data?.detail || e.message))
  }
  finally { clearTimeout(timeout); testingWebdav.value = false }
}

async function triggerBackup() {
  backingUp.value = true
  try {
    const res = await webdavApi.backup()
    if (res.success) message.success(res.message)
    else message.error(res.message)
    await refreshBackupList()
  } catch (e: any) { message.error("备份失败: " + (e.response?.data?.detail || e.message)) }
  finally { backingUp.value = false }
}

async function triggerBackupData() {
  backingUpData.value = true
  try {
    const res = await webdavApi.backupData()
    if (res.success) message.success(res.message)
    else message.error(res.message)
    await refreshBackupList()
  } catch (e: any) { message.error("备份失败: " + (e.response?.data?.detail || e.message)) }
  finally { backingUpData.value = false }
}

async function restoreFromBackup(name: string) {
  if (!confirm("确定要佽还原该数据目录备份吗？\n\n注意这将将替换整个数据库和文件目录！\n建议先手动备份当前数据")) return
  restoringData.value = true
  try {
    const res = await webdavApi.restoreData(name)
    if (res.success) {
      message.success(res.message)
    } else {
      message.error(res.message)
    }
  } catch (e: any) { message.error("还原失败: " + (e.response?.data?.detail || e.message)) }
  finally { restoringData.value = false }
}

async function refreshBackupList() {
  try {
    const res = await webdavApi.listBackups()
    backupList.value = res.files || []
  } catch {}
}

async function browseDir(path: string) {
  dirBrowser.value.loading = true
  dirBrowser.value.visible = true
  try {
    const payload: any = { path, url: webdav.value.url }
    if (webdav.value.username) payload.username = webdav.value.username
    if (webdav.value.password) payload.password = webdav.value.password
    const res = await webdavApi.browse(payload)
    dirBrowser.value.dirs = res.directories || []
    dirBrowser.value.currentPath = path
  } catch (e: any) {
    message.error("获取目录失败: " + (e.response?.data?.detail || e.message))
    dirBrowser.value.dirs = []
  }
  finally { dirBrowser.value.loading = false }
}

function selectDir(name: string) {
  const p = dirBrowser.value.currentPath.replace(/\/$/, "") + "/" + name
  webdav.value.backup_path = p
  dirBrowser.value.visible = false
}

function goUpDir() {
  const p = dirBrowser.value.currentPath.replace(/\/$/, "")
  const parent = p.substring(0, p.lastIndexOf("/")) || "/"
  browseDir(parent)
}

function isServerRoot(path: string) { return !path || path === '/' }

async function saveEmbedding() {
  try {
    await settingsApi.update("embedding", { settings: embedding.value })
    message.success("已保存")
  } catch { message.error("保存失败") }
}

async function testEmbedding() {
  if (!embedding.value.api_key) { message.warning("请先填写 API 密钥"); return }
  testing.value = true
  try {
    const res = await settingsApi.test("embedding", {
      provider: embedding.value.provider, model: embedding.value.model,
      api_key: embedding.value.api_key, api_url: embedding.value.api_url,
    })
    if (res.success) message.success(res.message)
    else message.error(res.message)
    if (res.detail) { showDetail.value = true; testResult.value = res }
  } catch (e: any) { message.error("请求失败: " + (e.response?.data?.detail || e.message)) }
  finally { testing.value = false }
}

async function startRebuild() {
  if (!confirm("确定要重建所有向量吗？所有向量数据将被清除")) return
  rebuilding.value = true; rebuildResult.value = ""
  try {
    const res = await api.post("/settings/embedding/rebuild", {
      provider: embedding.value.provider, model: embedding.value.model,
      dimension: embedding.value.dimension, api_key: embedding.value.api_key, api_url: embedding.value.api_url,
    })
    rebuildResult.value = res.data?.message || "开始重建"
    await loadVersions()
  } catch (e: any) { rebuildResult.value = "重建失败: " + (e.response?.data?.detail || e.message) }
  finally { rebuilding.value = false }
}

async function switchVersion(v: string) {
  if (!confirm("确定切换到版本" + v + "")) return
  switching.value = true
  try {
    await api.post("/settings/embedding/switch-version", null, { params: { version: v } })
    activeVersion.value = v
    message.success("切换成功")
  } catch (e: any) { message.error("切换失败: " + (e.response?.data?.detail || e.message)) }
  finally { switching.value = false }
}

async function deleteVersion(v: string) {
  if (!confirm("确定删除版本 " + v + "")) return
  try {
    await api.delete("/settings/embedding/old-version", { params: { version: v } })
    message.success("已删除" + v)
    await loadVersions()
  } catch (e: any) { message.error("删除失败: " + (e.response?.data?.detail || e.message)) }
}

async function handleLocalImport(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  importing.value = true
  try {
    const res = await webdavApi.importLocal(input.files[0])
    if (res.success) message.success(res.message)
    else message.error(res.message)
  } catch (e: any) { message.error("导入失败: " + (e.response?.data?.detail || e.message)) }
  finally { importing.value = false; input.value = '' }
}

async function importFromWebdav(name: string) {
  if (!confirm("确定要从文件导入吗")) return
  importing.value = true
  try {
    const res = await webdavApi.importWebdav(name)
    if (res.success) message.success(res.message)
    else message.error(res.message)
  } catch (e: any) { message.error("导入失败: " + (e.response?.data?.detail || e.message)) }
  finally { importing.value = false }
}
</script>
<template>
  <div class="settings-container" style="max-width:800px;margin:0 auto;padding:32px 20px">
    <div class="settings-layout">

      <!-- Top tab bar -->
      <div class="apple-tabs" style="display:flex;gap:2px;margin-bottom:20px;background:var(--apple-bg);padding:3px;border-radius:10px;border:1px solid var(--apple-border);width:fit-content;flex-wrap:wrap">
        <button v-for="cat in categories" :key="cat.key"
          style="padding:6px 14px;border-radius:8px;border:none;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:4px;transition:all 0.15s;background:transparent;color:var(--apple-text-secondary)"
          :style="activeTab === cat.key ? 'background:#fff;color:var(--apple-text-primary);font-weight:500;box-shadow:0 1px 3px rgba(0,0,0,0.06)' : 'color:var(--apple-text-secondary)'"
          @click="activeTab = cat.key">
          <component :is="cat.icon" :size="16" stroke-width="1.5" />
          {{ cat.label }}
        </button>
      </div>

      <!-- ===== WebDAV Backup ===== -->
      <div v-if="activeTab === 'webdav'" class="apple-card" style="background:var(--apple-card);border-radius:12px;padding:20px;border:1px solid var(--apple-border);margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:8px;font-weight:600;font-size:15px;margin-bottom:16px">
          <Cloud :size="18" stroke-width="1.5" />
          WebDAV 备份
        </div>

        <!-- URL + Username row -->
        <div style="display:flex;gap:12px;margin-bottom:14px">
          <div style="flex:1">
            <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">WebDAV 地址</label>
            <input v-model="webdav.url" class="apple-input" placeholder="https://example.com/dav/" style="width:100%" />
          </div>
          <div style="flex:1">
            <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">用户名</label>
            <input v-model="webdav.username" class="apple-input" placeholder="用户名" style="width:100%" />
          </div>
        </div>

        <!-- Password + Backup Path row -->
        <div style="display:flex;gap:12px;margin-bottom:14px">
          <div style="flex:1">
            <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">密码</label>
            <div style="position:relative">
              <input v-model="webdav.password" class="apple-input" :type="showPwd ? 'text' : 'password'" placeholder="密码" style="width:100%;padding-right:36px" />
              <button style="position:absolute;right:4px;top:50%;transform:translateY(-50%);padding:4px;background:transparent;border:none;color:var(--apple-text-tertiary);cursor:pointer;display:flex;align-items:center" @click="toggleShowPwd()">
                <EyeOff v-if="!showPwd" :size="16" stroke-width="1.5" />
                <Eye v-else :size="16" stroke-width="1.5" />
              </button>
            </div>
          </div>
          <div style="flex:1">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
              <label style="font-size:13px;color:var(--apple-text-secondary)">备份目录</label>
              <button style="padding:0 8px;height:24px;border-radius:6px;border:1px solid var(--apple-border);background:transparent;color:var(--apple-blue);font-size:11px;cursor:pointer;display:flex;align-items:center;gap:3px" @click="browseDir(webdav.backup_path || '/')">
                <FolderOpen :size="12" stroke-width="1.5" /> 浏览WebDAV目录
              </button>
            </div>
            <input v-model="webdav.backup_path" class="apple-input" placeholder="/backups" style="width:100%" />
          </div>
        </div>

        <!-- Auto backup toggle + schedule -->
        <div style="margin-bottom:14px">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
            <label style="font-size:13px;color:var(--apple-text-secondary)">自动备份</label>
            <div style="width:40px;height:24px;border-radius:12px;background:var(--apple-border);cursor:pointer;position:relative;transition:all 0.2s;flex-shrink:0"
              :style="backupEnabled ? 'background:#34c759' : 'background:#e8e8ed'"
              @click="backupEnabled = !backupEnabled">
              <div style="position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:10px;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.15);transition:all 0.2s"
                :style="backupEnabled ? 'transform:translateX(18px)' : ''"></div>
            </div>
          </div>
          <template v-if="backupEnabled">
            <div style="display:flex;gap:8px;align-items:center">
              <span style="font-size:13px;color:var(--apple-text-secondary)">将在每</span>
              <select v-model="webdav.schedule_frequency" class="apple-input" style="max-width:90px">
                <option value="daily">天</option>
                <option value="weekly">周</option>
                <option value="monthly">月</option>
              </select>
              <template v-if="webdav.schedule_frequency === 'weekly'">
                <select v-model="webdav.schedule_day" class="apple-input" style="max-width:80px">
                  <option value="1">周一</option>
                  <option value="2">周二</option>
                  <option value="3">周三</option>
                  <option value="4">周四</option>
                  <option value="5">周五</option>
                  <option value="6">周六</option>
                  <option value="7">周日</option>
                </select>
              </template>
              <template v-if="webdav.schedule_frequency === 'monthly'">
                <select v-model="webdav.schedule_day" class="apple-input" style="max-width:80px">
                  <option v-for="d in 31" :key="d" :value="d">{{ d }} 日</option>
                </select>
              </template>
              <span style="font-size:13px;color:var(--apple-text-secondary)">的</span>
              <input v-model="webdav.schedule_time" class="apple-input" type="time" style="max-width:110px" />
              <span style="font-size:13px;color:var(--apple-text-secondary)">自动备份</span>
            </div>
          </template>
        </div>

        <!-- Retention days -->
        <div style="margin-bottom:14px">
          <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:6px">备份保留期限</label>
          <div style="display:flex;gap:6px">
            <button :style="{'flex':1,'padding':'0 12px','height':'32px','border-radius':'8px','border':'1px solid ' + (webdav.retention_days === 7 ? '#007aff' : '#e8e8ed'),'background': webdav.retention_days === 7 ? '#007aff' : 'transparent','color': webdav.retention_days === 7 ? '#fff' : '#1d1d1f','font-size':'13px','cursor':'pointer'}" @click="webdav.retention_days = 7">7 天</button>
            <button :style="{'flex':1,'padding':'0 12px','height':'32px','border-radius':'8px','border':'1px solid ' + (webdav.retention_days === 30 ? '#007aff' : '#e8e8ed'),'background': webdav.retention_days === 30 ? '#007aff' : 'transparent','color': webdav.retention_days === 30 ? '#fff' : '#1d1d1f','font-size':'13px','cursor':'pointer'}" @click="webdav.retention_days = 30">30 天</button>
            <button :style="{'flex':1,'padding':'0 12px','height':'32px','border-radius':'8px','border':'1px solid ' + (webdav.retention_days === 0 ? '#007aff' : '#e8e8ed'),'background': webdav.retention_days === 0 ? '#007aff' : 'transparent','color': webdav.retention_days === 0 ? '#fff' : '#1d1d1f','font-size':'13px','cursor':'pointer'}" @click="webdav.retention_days = 0">永久保存</button>
          </div>
        </div>

        <!-- Action buttons -->
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <button style="display:flex;align-items:center;gap:6px;padding:0 16px;height:32px;border-radius:8px;border:none;background:var(--apple-blue);color:#fff;font-size:13px;cursor:pointer" @click="saveWebdav">
            <Cloud :size="14" stroke-width="1.5" /> 保存
          </button>
          <button style="display:flex;align-items:center;gap:6px;padding:0 16px;height:32px;border-radius:8px;border:1px solid var(--apple-border);background:transparent;color:var(--apple-text-primary);font-size:13px;cursor:pointer" :disabled="testingWebdav" @click="testWebdav">
            <RefreshCw :size="14" stroke-width="1.5" :style="testingWebdav ? 'animation:spin 1s linear infinite' : ''" /> {{ testingWebdav ? '测试中...' : '测试连接' }}
          </button>
          <button style="display:flex;align-items:center;gap:6px;padding:0 16px;height:32px;border-radius:8px;border:1px solid var(--apple-border);background:transparent;color:var(--apple-text-primary);font-size:13px;cursor:pointer" :disabled="backingUp" @click="triggerBackup">
            <Upload :size="14" stroke-width="1.5" /> {{ backingUp ? '备份中中...' : '立即备份' }}
          </button>
          <button style="display:flex;align-items:center;gap:6px;padding:0 16px;height:32px;border-radius:8px;border:1px solid var(--apple-orange, #ff9500);background:transparent;color:var(--apple-orange, #ff9500);font-size:13px;cursor:pointer" :disabled="backingUpData" @click="triggerBackupData">
            <Download :size="14" stroke-width="1.5" /> {{ backingUpData ? '备份中中...' : '备份数据目录' }}
          </button>
          <button style="display:flex;align-items:center;gap:6px;padding:0 16px;height:32px;border-radius:8px;border:1px solid var(--apple-border);background:transparent;color:var(--apple-text-primary);font-size:13px;cursor:pointer" @click="refreshBackupList">
            <RefreshCw :size="14" stroke-width="1.5" /> 刷新
          </button>
        </div>

        <!-- Backup file list -->
        <div v-if="backupList.length > 0" style="margin-top:12px;border:1px solid var(--apple-border);border-radius:8px;overflow:hidden;background:var(--apple-bg)">
          <div v-for="f in backupList" :key="f.name" style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--apple-border);font-size:13px">
            <span style="flex:1;word-break:break-all;display:flex;align-items:center;gap:6px">
              <span style="padding:0 6px;height:16px;line-height:16px;border-radius:3px;font-size:10px;font-weight:500;background:#ff950020;color:var(--apple-orange, #ff9500)" v-if="f.type === 'data'">数据</span>
              <span style="padding:0 6px;height:16px;line-height:16px;border-radius:3px;font-size:10px;font-weight:500;background:#007aff20;color:var(--apple-blue)" v-else>知识</span>
              {{ f.name }}
            </span>
            <template v-if="f.type === 'data'">
              <button style="padding:0 8px;height:24px;font-size:11px;border-radius:6px;border:1px solid var(--apple-orange, #ff9500);color:var(--apple-orange, #ff9500);background:transparent;cursor:pointer" @click="restoreFromBackup(f.href)">还原完整数据</button>
            </template>
            <template v-else>
              <button style="padding:0 8px;height:24px;font-size:11px;border-radius:6px;border:1px solid var(--apple-border);background:transparent;color:var(--apple-blue);cursor:pointer" @click="importFromWebdav(f.name)">导入知识</button>
            </template>
          </div>
        </div>
        <div v-else-if="!backupList.length" style="margin-top:12px;padding:8px 0;text-align:center;color:var(--apple-text-tertiary);font-size:13px">暂无备份文件，请鍏堥厤置 WebDAV 并执行备份</div>

        <!-- Local import -->
        <div style="margin-top:12px;display:flex;gap:8px;align-items:center">
          <label style="display:inline-flex;align-items:center;gap:6px;padding:0 16px;height:32px;border-radius:8px;border:1px solid var(--apple-blue);color:var(--apple-blue);font-size:13px;cursor:pointer">
            <Upload :size="14" stroke-width="1.5" />
            {{ importing ? '导入中...' : '从本地上传导入' }}
            <input type="file" accept=".json,.zip" style="display:none" :disabled="importing" @change="handleLocalImport" />
          </label>
        </div>
      </div>

      <!-- Directory Browser Modal -->
      <div v-if="dirBrowser.visible" style="position:fixed;top:0;left:0;right:0;bottom:0;z-index:1000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.3)" @click.self="dirBrowser.visible = false">
        <div style="background:#fff;border-radius:12px;padding:20px;width:400px;max-width:90vw;max-height:70vh;display:flex;flex-direction:column;box-shadow:0 10px 40px rgba(0,0,0,0.2)">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span style="font-weight:600;font-size:15px">选择备份目录</span>
            <button style="padding:4px;background:none;border:none;font-size:18px;cursor:pointer;color:#999" @click="dirBrowser.visible = false">&times;</button>
          </div>
          <div style="font-size:12px;color:var(--apple-text-secondary);margin-bottom:8px;word-break:break-all">
            当前路径: {{ dirBrowser.currentPath }}
          </div>
          <div v-if="dirBrowser.loading" style="text-align:center;padding:30px;color:#999">加载中...</div>
          <div v-else style="flex:1;overflow-y:auto">
            <div v-if="dirBrowser.currentPath !== '/'" style="display:flex;align-items:center;gap:6px;padding:8px 10px;border-radius:6px;cursor:pointer;font-size:13px" @click="goUpDir()">
              <FolderOpen :size="14" stroke-width="1.5" /> ..
            </div>
            <div v-for="d in dirBrowser.dirs" :key="d.name" style="display:flex;align-items:center;gap:6px;padding:8px 10px;border-radius:6px;cursor:pointer;font-size:13px;transition:background 0.15s" :style="{background: (webdav.backup_path.endsWith(d.name) || webdav.backup_path === dirBrowser.currentPath + '/' + d.name) ? '#f0f0f0' : 'transparent'}" @click="selectDir(d.name)" @mouseenter="$event.target.style.background='#f5f5f5'" @mouseleave="$event.target.style.background=''">
              <Folder :size="14" stroke-width="1.5" /> {{ d.name }}
            </div>
            <div v-if="!dirBrowser.loading && dirBrowser.dirs.length === 0" style="text-align:center;padding:20px;color:var(--apple-text-tertiary);font-size:12px">暂无子目录</div>
          </div>
          <div style="margin-top:12px;display:flex;gap:8px;justify-content:flex-end;border-top:1px solid #eee;padding-top:12px">
            <button style="padding:0 14px;height:32px;border-radius:8px;border:none;background:#ff3b30;color:#fff;font-size:13px;cursor:pointer" @click="dirBrowser.visible = false">取消</button>
            <button style="padding:0 14px;height:32px;border-radius:8px;border:none;background:#007aff;color:#fff;font-size:13px;cursor:pointer" @click="dirBrowser.visible = false">确定</button>
          </div>
        </div>
      </div>

      <!-- ===== Embedding ===== -->
      <div v-if="activeTab === 'embedding'" class="apple-card" style="background:var(--apple-card);border-radius:12px;padding:20px;border:1px solid var(--apple-border);margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:8px;font-weight:600;font-size:15px;margin-bottom:16px">
          <Cpu :size="18" stroke-width="1.5" />
          向量模型设置
        </div>
        <div style="margin-bottom:14px">
          <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">提供商</label>
          <select v-model="embedding.provider" class="apple-input" style="max-width:200px">
            <option value="openai">OpenAI</option>
            <option value="siliconflow">SiliconFlow</option>
            <option value="ollama">Ollama</option>
            <option value="doubao">Doubao (火山引擎)</option>
          </select>
        </div>
        <div style="margin-bottom:14px">
          <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">API 地址</label>
          <input v-model="embedding.api_url" class="apple-input" placeholder="https://api.openai.com/v1" style="width:100%" />
        </div>
        <div style="margin-bottom:14px">
          <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">API 密钥</label>
          <input v-model="embedding.api_key" class="apple-input" type="password" placeholder="sk-..." style="width:100%" />
        </div>
        <div style="margin-bottom:14px">
          <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">模型名称</label>
          <input v-model="embedding.model" class="apple-input" placeholder="text-embedding-3-small" style="width:100%" />
        </div>
        <div style="display:flex;gap:12px;margin-bottom:14px">
          <div>
            <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">向量维度</label>
            <input v-model.number="embedding.dimension" class="apple-input" type="number" min="64" max="4096" style="max-width:100px" />
          </div>
          <div>
            <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">批量大小</label>
            <input v-model.number="embedding.batch_size" class="apple-input" type="number" min="1" max="100" style="max-width:80px" />
          </div>
          <div>
            <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">超时(秒)</label>
            <input v-model.number="embedding.timeout" class="apple-input" type="number" min="5" max="120" style="max-width:80px" />
          </div>
        </div>
        <div style="display:flex;gap:8px">
          <button style="display:flex;align-items:center;gap:6px;padding:0 16px;height:32px;border-radius:8px;border:none;background:var(--apple-blue);color:#fff;font-size:13px;cursor:pointer" @click="saveEmbedding">
            <Cloud :size="14" stroke-width="1.5" /> 保存
          </button>
          <button style="display:flex;align-items:center;gap:6px;padding:0 16px;height:32px;border-radius:8px;border:1px solid var(--apple-border);background:transparent;color:var(--apple-text-primary);font-size:13px;cursor:pointer" :disabled="testing" @click="testEmbedding">
            <RefreshCw :size="14" stroke-width="1.5" :style="testing ? 'animation:spin 1s linear infinite' : ''" /> {{ testing ? '测试中...' : '测试连接' }}
          </button>
        </div>

        <!-- Vector rebuild -->
        <div style="border-top:1px solid var(--apple-border);padding-top:16px;margin-top:16px">
          <div style="display:flex;align-items:center;gap:8px;font-size:14px;font-weight:500;margin-bottom:12px">
            <RefreshCw :size="16" stroke-width="1.5" />
            向量重建
          </div>
          <button style="display:flex;align-items:center;gap:6px;padding:0 16px;height:32px;border-radius:8px;border:none;color:#fff;font-size:13px;cursor:pointer;background:var(--apple-orange, #ff9500)" :disabled="rebuilding" @click="startRebuild">
            {{ rebuilding ? '重建中...' : '开始重建向量' }}
          </button>
          <div v-if="rebuildResult" style="padding:10px 14px;background:#f0fff4;border:1px solid #34c759;border-radius:8px;margin-top:12px;font-size:13px;color:#1a7d36">{{ rebuildResult }}</div>
          <div v-if="versions.length > 0" style="margin-top:12px">
            <div style="font-weight:500;font-size:12px;margin-bottom:8px;color:var(--apple-text-tertiary)">向量版本列表</div>
            <div v-for="v in versions" :key="v.name" style="display:flex;align-items:center;gap:12px;padding:10px 14px;margin-bottom:4px;background:var(--apple-bg);border-radius:8px;font-size:13px">
              <span style="padding:1px 8px;border-radius:4px;font-size:11px;background:var(--apple-border);color:var(--apple-text-secondary)" :style="v.name === activeVersion ? 'background:var(--apple-blue);color:white' : ''">{{ v.name }}</span>
              <span style="color:var(--apple-text-secondary)">{{ v.count }} 条</span>
              <span style="color:var(--apple-text-tertiary);font-size:12px">{{ v.latest ? new Date(v.latest).toLocaleString() : '' }}</span>
              <div style="margin-left:auto;display:flex;gap:6px">
                <button v-if="v.name !== activeVersion" style="padding:0 10px;height:26px;font-size:11px;border-radius:6px;border:1px solid var(--apple-border);background:transparent;cursor:pointer" @click="switchVersion(v.name)">切换</button>
                <button v-if="v.name !== 'v1'" style="padding:0 10px;height:26px;font-size:11px;border-radius:6px;border:1px solid #ff3b30;color:#ff3b30;background:transparent;cursor:pointer" @click="deleteVersion(v.name)">删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== Retriever ===== -->
      <div v-if="activeTab === 'retriever'" class="apple-card" style="background:var(--apple-card);border-radius:12px;padding:20px;border:1px solid var(--apple-border);margin-bottom:16px">
        <div style="font-weight:600;font-size:15px;margin-bottom:16px">检索设置</div>
        <div style="margin-bottom:14px">
          <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">返回数量</label>
          <input v-model.number="retriever.top_k" class="apple-input" type="number" min="1" max="50" style="max-width:100px" />
        </div>
      </div>

      <!-- ===== Graph ===== -->
      <div v-if="activeTab === 'graph'" class="apple-card" style="background:var(--apple-card);border-radius:12px;padding:20px;border:1px solid var(--apple-border);margin-bottom:16px">
        <div style="font-weight:600;font-size:15px;margin-bottom:16px">图谱设置</div>
        <div style="margin-bottom:14px">
          <label style="display:block;font-size:13px;color:var(--apple-text-secondary);margin-bottom:4px">每页最大节点数</label>
          <input v-model.number="graph.max_nodes" class="apple-input" type="number" min="50" max="1000" style="max-width:100px" />
        </div>
      </div>

      <!-- ===== About ===== -->
      <div v-if="activeTab === 'about'" class="apple-card" style="background:var(--apple-card);border-radius:12px;padding:20px;border:1px solid var(--apple-border);margin-bottom:16px">
        <div style="font-weight:600;font-size:15px;margin-bottom:12px">关于</div>
        <div style="line-height:2;font-size:14px">
          <div><strong style="font-size:15px">AI Knowledge Hub v1.0</strong></div>
          <div style="color:var(--apple-text-secondary);font-size:13px">FastAPI + Vue3 + SQLite</div>
          <div style="color:var(--apple-text-secondary);font-size:13px">MCP: HTTP/SSE + FTS5 全文搜索</div>
        </div>
      </div>
    </div>
  </div>
</template>
<style scoped>
@keyframes spin {
  from { transform: rotate(0deg) }
  to { transform: rotate(360deg) }
}
</style>

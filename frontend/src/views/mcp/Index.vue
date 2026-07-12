<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { mcpApi } from '../../api'
import api from '../../api'

const config = ref<any>({})
const resetKeyResult = ref('')
const resetting = ref(false)
const message = useMessage()

const mcpUrl = computed(() => config.value?.mcp_url || '')

const mcpConfigStr = computed(() => {
  const name = config.value?.name || 'ai-knowledge-hub'
  const url = mcpUrl.value || config.value?.endpoints?.http + '/sse' || ''
  return JSON.stringify({ mcpServers: { [name]: { url } } }, null, 2)
})

function copyText(text: string) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => message.success('已复制'))
  } else {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    try { document.execCommand('copy'); message.success('已复制') } catch { message.error('复制失败') }
    document.body.removeChild(ta)
  }
}

async function load() {
  try { config.value = await mcpApi.config() } catch {}
}
onMounted(load)

function copyMcpUrl() { copyText(mcpUrl.value) }

async function resetKey() {
  if (!window.confirm('确定要重置 MCP 密钥吗？重置后原密钥将立即作废。')) return
  resetting.value = true
  resetKeyResult.value = ''
  try {
    const res = await api.post('/mcp/reset-key')
    resetKeyResult.value = res.data.mcp_key
    try { config.value = await mcpApi.config() } catch {}
    message.success('密钥已重置')
  } catch {
    message.error('重置失败')
  } finally { resetting.value = false }
}

const mcpTools = [
  'search_knowledge','semantic_search','hybrid_search','keyword_search','graph_search',
  'search_by_tag','search_by_collection','get_document','get_chunk','get_related',
  'create_document','update_document','delete_document',
  'create_entity','create_relation','create_tag',
  'remember','recall','forget','find_neighbors','find_path','graph_statistics','statistics'
]
</script>

<template>
  <div>
    <div class="apple-card" style="margin-bottom:16px">
      <p style="margin:0 0 16px;color:var(--apple-text-secondary);font-size:14px;line-height:1.6">
        通过 MCP 协议，你可以让 AI 助手直接调用此解析器的能力。请注意保护你的密钥。
      </p>
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:16px">
        <input :value="mcpUrl" readonly class="apple-input" placeholder="加载中..." style="font-family:var(--font-family-mono)" />
        <button class="apple-btn" @click="copyMcpUrl" :disabled="!mcpUrl">复制</button>
        <button class="apple-btn" style="background:transparent;border:1px solid #ffd60a;color:#d49b00" @click="resetKey" :disabled="resetting || !mcpUrl">
          {{ resetting ? '重置中...' : '重置密钥' }}
        </button>
      </div>

      <div v-if="resetKeyResult" class="apple-card" style="background:#fffbe6;border-color:#ffd60a;margin-bottom:16px">
        <div style="font-weight:500;margin-bottom:8px;font-size:13px;color:#b8860b">新密钥已生成 — 原密钥已作废，请立即复制保存</div>
        <div style="display:flex;gap:8px;align-items:center">
          <input :value="resetKeyResult" readonly class="apple-input" style="font-family:var(--font-family-mono)" />
          <button class="apple-btn" @click="copyText(resetKeyResult)">复制</button>
        </div>
      </div>

      <div class="apple-card-title" style="margin-bottom:8px">客户端配置</div>
      <pre style="background:#1d1d1f;color:#f5f5f7;padding:16px;border-radius:8px;font-size:12px;font-family:'SF Mono','Fira Code',monospace;overflow-x:auto;margin:0">{{ mcpConfigStr }}</pre>
      <div style="margin-top:12px;padding:10px 14px;background:var(--apple-bg);border-radius:8px;font-size:13px;color:var(--apple-text-secondary)">
        将以上配置添加到 AI 助手的 MCP 配置文件中即可使用。
      </div>
    </div>

    <div class="apple-card">
      <div class="apple-card-title">可用工具 ({{ mcpTools.length }})</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;max-height:200px;overflow-y:auto">
        <span v-for="t in mcpTools" :key="t" class="apple-tag">{{ t }}</span>
      </div>
    </div>
  </div>

    <!-- Stdio Config Card -->
    <div class="dash-card" style="margin-top:24px">
      <div class="dash-card-header">
        <div class="dash-card-title-row">
          <Server :size="16" color="#8B5CF6" />
          <span>标准 MCP 配置（Claude Desktop / Cursor）</span>
        </div>
      </div>
      <div style="font-size:13px;color:#64748B;margin-bottom:12px;line-height:1.5">
        下载 <code style="background:#F1F5F9;padding:2px 6px;border-radius:4px;font-size:12px">mcp_stdio_client.py</code>
        并配置到你的 MCP 客户端中，即可让 AI 助手直接连接本知识库。
      </div>
      <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:16px;font-family:ui-monospace,'SF Mono',monospace;font-size:12px;line-height:1.6;white-space:pre;overflow-x:auto;margin-bottom:12px">
{
  "mcpServers": {
    "ai-knowledge-hub": {
      "command": "python",
      "args": [
        "/path/to/mcp_stdio_client.py",
        "--url", "{{ serverUrl }}",
        "--key", "{{ mcpKey }}"
      ]
    }
  }
}
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="apple-btn-primary" @click="copyStdioConfig" style="background:#8B5CF6">
          <Clipboard :size="14" />
          复制配置
        </button>
      </div>
    </div>

</template>
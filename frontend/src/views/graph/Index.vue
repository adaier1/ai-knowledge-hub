�<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { graphApi, knowledgeApi } from '../../api'
import { Search, RotateCcw } from '@lucide/vue'

const router = useRouter()
const containerRef = ref<HTMLDivElement>()
let cy: any = null
const selectedNode = ref<any>(null)
const nodeDetail = ref<any>(null)
const searchQuery = ref('')
const depth = ref(1)
const loading = ref(false)
const nodeCount = ref(0)
const edgeCount = ref(0)
const hoveredId = ref<string | null>(null)

const COLOR_PALETTE = [
  '#0071e3', '#34c759', '#ff9f0a', '#ff3b30',
  '#5ac8fa', '#af52de', '#ff2d55', '#5856d6',
  '#00c7be', '#ff9500', '#64d2ff', '#30d158',
]
const HOVER_COLORS = [
  '#4a9eff', '#6ddc8b', '#ffb84d', '#ff6b5b',
  '#8adaff', '#d48cff', '#ff6b8a', '#8a8aff',
  '#4ae8dd', '#ffbf4d', '#8ae0ff', '#6dec7a',
]
const LIGHT_GRAY = '#d4d4d4'
const TAG_COLOR = '#c7c7c7'

function getColorByDegree(degree: number, maxDegree: number): string {
  if (maxDegree === 0) return COLOR_PALETTE[0]
  const ratio = Math.min(degree / maxDegree, 1)
  const idx = Math.floor(ratio * (COLOR_PALETTE.length - 1))
  return COLOR_PALETTE[idx]
}

function getHoverColor(degree: number, maxDegree: number): string {
  if (maxDegree === 0) return HOVER_COLORS[0]
  const ratio = Math.min(degree / maxDegree, 1)
  const idx = Math.floor(ratio * (HOVER_COLORS.length - 1))
  return HOVER_COLORS[idx]
}

function initCy() {
  if (!containerRef.value) return
  import('cytoscape').then((cytoscape: any) => {
    const cyInstance = cytoscape.default || cytoscape
    cy = cyInstance({
      container: containerRef.value,
      style: [
        { selector: 'node', style: {
          'background-color': '#0071e3',
          label: 'data(label)',
          color: '#aeaeb2',
          'font-size': '7px',
          'text-valign': 'bottom',
          'text-margin-y': 3,
          'font-family': '-apple-system, BlinkMacSystemFont, SF Pro Text, PingFang SC, sans-serif',
          'font-weight': 300,
          width: 6,
          height: 6,
          'border-width': 0,
          'transition-property': 'opacity, width, height, background-color, color',
          'transition-duration': '0.2s',
        }},
        { selector: 'node[kind = "tag"]', style: { 'background-color': TAG_COLOR, width: 4, height: 4 }},
        { selector: 'node.hover', style: {
          width: 10,
          height: 10,
          'font-size': '9px',
          'font-weight': 500,
          color: '#1d1d1f',
          'shadow-blur': 10,
          'shadow-color': 'rgba(0,0,0,0.08)',
          'shadow-offset-x': 0,
          'shadow-offset-y': 0,
        }},
        { selector: 'node:selected', style: {
          'border-width': 0,
          'shadow-blur': 14, 'shadow-color': 'rgba(0,113,227,0.3)', 'shadow-offset-x': 0, 'shadow-offset-y': 0,
          width: 10, height: 10,
          'font-size': '9px',
          'font-weight': 500,
          color: '#1d1d1f',
        }},
        { selector: 'node.highlighted', style: { opacity: 1 }},
        { selector: 'node.dimmed', style: { opacity: 0.06 }},
        { selector: 'edge', style: {
          width: 0.6,
          'line-color': LIGHT_GRAY,
          'curve-style': 'haystack',
          'haystack-radius': 0.5,
          'transition-property': 'opacity',
          'transition-duration': '0.15s',
        }},
        { selector: 'edge[kind = "shared_tag"]', style: { 'line-color': LIGHT_GRAY, width: 0.4, 'line-style': 'dotted' }},
        { selector: 'edge[kind = "tag"]', style: { 'line-color': LIGHT_GRAY, width: 0.5 }},
        { selector: 'edge.highlighted', style: { opacity: 0.5 }},
        { selector: 'edge.dimmed', style: { opacity: 0.01 }},
      ],
      layout: { name: 'preset' },
      minZoom: 0.1,
      maxZoom: 8,
      wheelSensitivity: 0.3,
    })

    cy.on('tap', 'node', (evt: any) => {
      const node = evt.target
      selectedNode.value = { id: node.id(), label: node.data('label') }
      const parts = node.id().split('_')
      loadNodeDetail(parts[0], parseInt(parts[1]))
    })
    cy.on('tap', (evt: any) => {
      if (evt.target === cy) { selectedNode.value = null; nodeDetail.value = null }
    })

    cy.on('mouseover', 'node', (evt: any) => {
      const node = evt.target
      const nid = node.id()
      if (hoveredId.value === nid) return
      hoveredId.value = nid
      // Enlarge and change color on hover
      const degree = node.degree()
      const maxDegree = Math.max(...cy.nodes().map((n: any) => n.degree()), 1)
      const hoverColor = getHoverColor(degree, maxDegree)
      node.style('background-color', hoverColor)
      node.addClass('hover')
      // Dim non-connected nodes
      const connectedEdges = node.connectedEdges()
      const connectedNodes = node.neighborhood().add(node)
      cy.nodes().not(connectedNodes).addClass('dimmed').removeClass('highlighted')
      connectedNodes.removeClass('dimmed').addClass('highlighted')
      cy.edges().not(connectedEdges).addClass('dimmed').removeClass('highlighted')
      connectedEdges.removeClass('dimmed').addClass('highlighted')
    })
    cy.on('mouseout', 'node', (evt: any) => {
      const node = evt.target
      hoveredId.value = null
      // Reset node color to its original degree-based color
      const degree = node.degree()
      const maxDegree = Math.max(...cy.nodes().map((n: any) => n.degree()), 1)
      const origColor = getColorByDegree(degree, maxDegree)
      node.style('background-color', origColor)
      node.removeClass('hover')
      cy.elements().removeClass('dimmed highlighted')
    })

    requestAnimationFrame(() => loadGraph())
  })
}

async function loadGraph(centerId?: number) {
  loading.value = true
  try {
    const res = await graphApi.get({ center_id: centerId, depth: depth.value, limit: 200 })
    if (!cy) return
    cy.elements().remove()
    const nodes = (res.nodes || []).map((n: any) => ({
      group: 'nodes', data: { id: n.id, label: n.label, kind: n.type, weight: n.size || 1 }
    }))
    const edges = (res.edges || []).map((e: any) => ({
      group: 'edges', data: { id: e.id, source: e.source, target: e.target, label: e.label, kind: e.type }
    }))
    nodeCount.value = nodes.length
    edgeCount.value = edges.length
    cy.add([...nodes, ...edges])

    const maxDegree = Math.max(...cy.nodes().map((n: any) => n.degree()), 1)
    cy.nodes().forEach((n: any) => {
      if (n.data('kind') !== 'tag') {
        const color = getColorByDegree(n.degree(), maxDegree)
        n.style('background-color', color)
      }
    })

    // Spherical concentric layout
    cy.layout({
      name: 'concentric',
      animate: false,
      concentric: (n: any) => n.degree(),
      levelWidth: () => 1.2,
      spacing: 90,
      avoidOverlap: true,
    }).run()

    // Simulate 3D depth: outer rings smaller and lighter
    setTimeout(() => {
      const levels: Record<number, number> = {}
      cy.nodes().forEach((n: any) => {
        const pos = n.position()
        const dist = Math.sqrt(pos.x * pos.x + pos.y * pos.y)
        const level = Math.round(dist / 90)
        levels[level] = (levels[level] || 0) + 1
      })
      const maxLevel = Math.max(...Object.keys(levels).map(Number), 1)
      cy.nodes().forEach((n: any) => {
        const pos = n.position()
        const dist = Math.sqrt(pos.x * pos.x + pos.y * pos.y)
        const level = Math.round(dist / 90)
        const depthRatio = level / maxLevel
        const size = Math.max(4, 8 - depthRatio * 4)
        const opacity = Math.max(0.35, 1 - depthRatio * 0.5)
        n.style('width', size)
        n.style('height', size)
        n.style('opacity', opacity)
      })
      cy.fit(undefined, 60)
      cy.center()
    }, 80)
  } catch {}
  finally { loading.value = false }
}

async function loadNodeDetail(type: string, id: number) {
  if (type === 'knowledge') { try { nodeDetail.value = await knowledgeApi.get(id) } catch { nodeDetail.value = null } }
  else { nodeDetail.value = null }
}

async function doSearch() {
  if (!searchQuery.value) return
  const res = await knowledgeApi.list({ search: searchQuery.value, limit: 5 })
  if (res.items?.length > 0) await loadGraph(res.items[0].id)
}

function resetView() {
  if (cy) { cy.fit(undefined, 60); cy.center() }
  selectedNode.value = null
  nodeDetail.value = null
}

onMounted(() => { nextTick(() => initCy()) })
onUnmounted(() => { if (cy) cy.destroy() })
</script>

<template>
  <div class="graph-page">
    <div class="graph-toolbar">
      <div class="graph-stats">
        <span class="stat-dot"></span>
        {{ nodeCount }} 节点 / {{ edgeCount }} 关系
      </div>
      <div class="graph-actions">
        <div class="search-box">
          <Search :size="13" class="search-icon" stroke-width="1.5" />
          <input v-model="searchQuery" class="search-input" placeholder="搜索节点..." @keyup.enter="doSearch" />
        </div>
        <select v-model="depth" class="depth-select">
          <option :value="1">深度 1</option>
          <option :value="2">深度 2</option>
        </select>
        <button class="toolbar-btn" @click="loadGraph()">
          <RotateCcw :size="12" stroke-width="1.5" /> 重置
        </button>
      </div>
    </div>

    <div class="graph-body">
      <div ref="containerRef" class="graph-canvas"></div>
      <div v-if="selectedNode" class="detail-panel">
        <div class="detail-header">
          <span class="detail-title">{{ selectedNode.label }}</span>
          <button class="detail-close" @click="selectedNode=null">&times;</button>
        </div>
        <div v-if="nodeDetail" class="detail-body">
          <div class="detail-row"><span class="detail-label">来源</span><span>{{ nodeDetail.source || '-' }}</span></div>
          <div class="detail-row"><span class="detail-label">片段</span><span>{{ nodeDetail.chunk_count || 0 }}</span></div>
          <button class="detail-open" @click="router.push('/knowledge/'+nodeDetail.id)">打开文档</button>
        </div>
        <div v-else class="detail-empty">鐐瑰嚮节点鏌�湅璇=儏</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.graph-page { display:flex; flex-direction:column; height:100%; }
.graph-toolbar { display:flex; align-items:center; justify-content:space-between; padding:0 0 12px 0; }
.graph-stats { font-size:12px; color:#8e8e93; display:flex; align-items:center; gap:6px; }
.stat-dot { width:6px; height:6px; border-radius:50%; background:#34c759; display:inline-block; }
.graph-actions { display:flex; align-items:center; gap:8px; }
.search-box { position:relative; }
.search-icon { position:absolute; left:10px; top:50%; transform:translateY(-50%); color:#aeaeb2; pointer-events:none; }
.search-input { width:160px; height:30px; padding-left:30px; border:1px solid #e5e5ea; border-radius:8px; font-size:12px; color:#1d1d1f; background:#ffffff; outline:none; }
.search-input:focus { border-color:#0071e3; }
.search-input::placeholder { color:#aeaeb2; }
.depth-select { height:30px; border:1px solid #e5e5ea; border-radius:8px; font-size:12px; color:#1d1d1f; background:#ffffff; outline:none; cursor:pointer; padding:0 8px; }
.depth-select:focus { border-color:#0071e3; }
.toolbar-btn { display:flex; align-items:center; gap:4px; padding:0 14px; height:30px; border:1px solid #e5e5ea; border-radius:8px; font-size:12px; color:#1d1d1f; background:#ffffff; cursor:pointer; }
.toolbar-btn:hover { background:#f5f5f7; border-color:#d1d1d6; }
.graph-body { flex:1; display:flex; gap:12px; min-height:0; }
.graph-canvas { flex:1; background:#ffffff; border:1px solid #f0f0f0; border-radius:12px; min-height:300px; overflow:hidden; }
.detail-panel { width:240px; flex-shrink:0; border:1px solid #f0f0f0; border-radius:12px; background:#ffffff; height:fit-content; overflow:hidden; }
.detail-header { display:flex; justify-content:space-between; align-items:center; padding:14px; border-bottom:1px solid #f0f0f0; }
.detail-title { font-size:13px; font-weight:500; color:#1d1d1f; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.detail-close { width:22px; height:22px; border-radius:6px; border:none; background:transparent; color:#aeaeb2; cursor:pointer; font-size:16px; display:flex; align-items:center; justify-content:center; }
.detail-close:hover { background:#f5f5f7; color:#1d1d1f; }
.detail-body { padding:14px; font-size:12px; }
.detail-row { display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #f5f5f7; color:#636366; }
.detail-label { color:#aeaeb2; }
.detail-open { margin-top:12px; width:100%; padding:8px 0; border:none; border-radius:8px; background:#0071e3; color:#fff; font-size:12px; cursor:pointer; }
.detail-open:hover { background:#0077ed; }
.detail-empty { padding:14px; font-size:12px; color:#aeaeb2; }
</style>

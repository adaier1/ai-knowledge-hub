<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useMessage } from 'naive-ui'

const message = useMessage()

function handler(e: Event) {
  const detail = (e as CustomEvent).detail
  if (detail?.type === 'error') message.error(detail.content || 'Error')
  else if (detail?.type === 'success') message.success(detail.content || 'Success')
  else if (detail?.type === 'warning') message.warning(detail.content || 'Warning')
  else message.info(detail?.content || 'Info')
}

onMounted(() => window.addEventListener('show-message', handler))
onUnmounted(() => window.removeEventListener('show-message', handler))
</script>
<template><div style="display:none"></div></template>

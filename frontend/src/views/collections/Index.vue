<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { NButton, NModal, NForm, NFormItem, NInput, NColorPicker, NDataTable, NPopconfirm } from 'naive-ui'
import { collectionApi } from '../../api'

const items = ref<any[]>([])
const showModal = ref(false)
const form = ref({ name: '', description: '', color: '#18a058' })

async function load() { try { const r = await collectionApi.list(); items.value = r.items } catch {} }
onMounted(load)
async function save() { try { await collectionApi.create(form.value); showModal.value = false; load() } catch {} }

const columns = [
  { title: '名称', key: 'name' },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  { title: '颜色', key: 'color', render: (r: any) => h('div', {style:{width:20,height:20,borderRadius:4,background:r.color}}) },
  { title: '项目数', key: 'knowledge_count', width: 70 },
  { title: '操作', key: 'actions', render: (r: any) => h(NPopconfirm, {onPositiveClick: () => del(r.id)}, {trigger: () => h(NButton, {size:'tiny', type:'error'}, {default: () => '删除'}), default: () => '确认删除？'}) },
]

async function del(id: number) { try { await collectionApi.delete(id); load() } catch {} }
</script>

<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h2 class="text-xl font-bold">集合管理</h2>
      <NButton type="primary" @click="showModal = true">+ 新建</NButton>
    </div>
    <NDataTable :columns="columns" :data="items" striped />
    <NModal v-model:show="showModal" title="新建集合" preset="card" style="width:450px">
      <NForm :model="form">
        <NFormItem label="名称"><NInput v-model:value="form.name" /></NFormItem>
        <NFormItem label="描述"><NInput v-model:value="form.description" type="textarea" :rows="2" /></NFormItem>
        <NFormItem label="颜色"><NColorPicker v-model:value="form.color" /></NFormItem>
      </NForm>
      <NButton type="primary" @click="save">创建</NButton>
    </NModal>
  </div>
</template>

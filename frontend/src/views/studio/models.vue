<!-- 模型中心：四分区统一管理，各功能页仅引用 -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>{{ $t('studio.models.title') }}</h1>
        <p class="desc">{{ $t('studio.models.desc') }}</p>
      </div>
      <div class="header-actions">
        <ElButton @click="$router.push('/manage/help')">{{ $t('studio.models.helpBtn') }}</ElButton>
        <ElButton @click="syncCheckpoints" :loading="syncing">{{ $t('studio.models.syncBtn') }}</ElButton>
        <ElButton type="primary" @click="openAdd">{{ $t('studio.models.addBtn') }}</ElButton>
      </div>
    </div>

    <!-- 统计卡 -->
    <div class="stat-grid">
      <div class="studio-card stat-card">
        <div class="stat-label">{{ $t('studio.models.stat.count', { category: categoryText(activeTab) }) }}</div>
        <div class="stat-num blue">{{ countBy(activeTab) }}</div>
        <div class="stat-sub">{{ $t('studio.models.stat.total', { total: models.length, checkpoint: countBy('checkpoint'), lora: countBy('lora'), translate: countBy('translate'), matting: countBy('matting') }) }}</div>
      </div>
      <div class="studio-card stat-card">
        <div class="stat-label">{{ $t('studio.models.stat.enabled') }}</div>
        <div class="stat-num cyan">{{ models.filter((m) => isEnabled(m)).length }}</div>
        <div class="stat-sub">{{ $t('studio.models.stat.enabledHint') }}</div>
      </div>
      <div class="studio-card stat-card">
        <div class="stat-label">{{ $t('studio.models.stat.endpoint') }}</div>
        <div class="stat-num purple" style="font-size: 16px; line-height: 40px">ComfyUI :8188</div>
        <div class="stat-sub">{{ $t('studio.models.stat.endpointHint') }}</div>
      </div>
    </div>

    <!-- 分区 tabs -->
    <div class="tabs-row">
      <div
        v-for="cat in categories"
        :key="cat.key"
        class="tab-item"
        :class="{ on: activeTab === cat.key }"
        @click="activeTab = cat.key"
      >
        {{ cat.label }}
      </div>
    </div>

    <div class="studio-card table-card">
      <ElTable :data="filteredModels" style="width: 100%">
        <ElTableColumn prop="name" :label="$t('studio.models.table.name')" min-width="180">
          <template #default="{ row }">
            <span class="model-name">{{ row.name }}</span>
            <span v-if="isEnabled(row, 'is_default')" class="badge default">{{ $t('studio.models.table.default') }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="category" :label="$t('studio.models.table.category')" width="110">
          <template #default="{ row }">
            <span class="badge" :class="categoryBadge(row.category)">{{ categoryText(row.category) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="meta" :label="$t('studio.models.table.meta')" min-width="220">
          <template #default="{ row }">
            <!-- 翻译模型：结构化摘要，api_key 打码 -->
            <template v-if="row.category === 'translate' && parseMeta(row).base_url">
              <div class="meta-text translate-meta">
                <div><span class="meta-key">{{ $t('studio.models.table.api') }}</span>{{ parseMeta(row).base_url }}</div>
                <div><span class="meta-key">{{ $t('studio.models.table.model') }}</span>{{ parseMeta(row).model_id || '—' }}</div>
                <div><span class="meta-key">{{ $t('studio.models.table.key') }}</span>{{ maskKey(parseMeta(row).api_key) }}</div>
              </div>
            </template>
            <span v-else class="meta-text">{{ row.meta && row.meta !== '{}' ? row.meta : '—' }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn :label="$t('studio.models.table.enabled')" width="90">
          <template #default="{ row }">
            <ElSwitch :model-value="isEnabled(row)" @change="(v: any) => toggleEnabled(row, v)" />
          </template>
        </ElTableColumn>
        <ElTableColumn :label="$t('studio.models.table.actions')" width="200" fixed="right">
          <template #default="{ row }">
            <ElButton
              size="small"
              :disabled="isEnabled(row, 'is_default')"
              @click="setDefault(row)"
            >
              {{ $t('studio.models.table.setDefault') }}
            </ElButton>
            <ElButton size="small" type="primary" plain @click="openEdit(row)">{{ $t('studio.models.table.edit') }}</ElButton>
            <ElButton size="small" type="danger" plain @click="remove(row)">{{ $t('studio.common.actions.delete') }}</ElButton>
          </template>
        </ElTableColumn>
      </ElTable>
    </div>

    <!-- 新增模型 -->
    <ElDialog v-model="addVisible" :title="$t('studio.models.dialog.addTitle')" width="500px">
      <ElForm label-width="80px">
        <ElFormItem :label="$t('studio.models.dialog.category')">
          <ElSelect v-model="addForm.category" style="width: 100%" @change="onAddCategoryChange">
            <ElOption v-for="cat in categories" :key="cat.key" :label="cat.label" :value="cat.key" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem :label="$t('studio.models.dialog.name')">
          <ElInput v-model="addForm.name" :placeholder="$t('studio.models.placeholder.name')" />
        </ElFormItem>

        <!-- 翻译模型：结构化配置（OpenAI 兼容接口） -->
        <template v-if="addForm.category === 'translate'">
          <ElFormItem :label="$t('studio.models.dialog.baseUrl')">
            <ElInput v-model="addForm.base_url" :placeholder="$t('studio.models.placeholder.baseUrl')" />
          </ElFormItem>
          <ElFormItem label="API Key">
            <ElInput
              v-model="addForm.api_key"
              type="password"
              show-password
              :placeholder="$t('studio.models.placeholder.apiKeyTip')"
            />
          </ElFormItem>
          <ElFormItem :label="$t('studio.models.dialog.modelId')">
            <ElInput v-model="addForm.model_id" :placeholder="$t('studio.models.placeholder.modelId')" />
          </ElFormItem>
          <ElFormItem :label="$t('studio.models.dialog.remark')">
            <ElInput v-model="addForm.meta" type="textarea" :rows="2" :placeholder="$t('studio.models.placeholder.remark')" />
          </ElFormItem>
          <div class="form-tip">
            {{ $t('studio.models.tip.translate') }}
            <ElLink type="primary" @click="$router.push('/manage/help')">{{ $t('studio.models.tip.helpLink') }}</ElLink>
          </div>
        </template>

        <!-- 其他类别：自由 JSON -->
        <ElFormItem v-else :label="$t('studio.models.dialog.meta')">
          <ElInput v-model="addForm.meta" type="textarea" :rows="2" :placeholder="$t('studio.models.placeholder.meta')" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="addVisible = false">{{ $t('studio.common.actions.cancel') }}</ElButton>
        <ElButton type="primary" :loading="adding" @click="submitAdd">{{ $t('studio.models.dialog.confirmAdd') }}</ElButton>
      </template>
    </ElDialog>

    <!-- 编辑模型 -->
    <ElDialog v-model="editVisible" :title="$t('studio.models.dialog.editTitle', { name: editForm.name })" width="500px">
      <ElForm label-width="80px">
        <ElFormItem :label="$t('studio.models.dialog.name')">
          <ElInput v-model="editForm.name" />
        </ElFormItem>
        <template v-if="editForm.category === 'translate'">
          <ElFormItem :label="$t('studio.models.dialog.baseUrl')">
            <ElInput v-model="editForm.base_url" :placeholder="$t('studio.models.placeholder.baseUrl')" />
          </ElFormItem>
          <ElFormItem label="API Key">
            <ElInput
              v-model="editForm.api_key"
              type="password"
              show-password
              :placeholder="$t('studio.models.placeholder.apiKeyKeep')"
            />
          </ElFormItem>
          <ElFormItem :label="$t('studio.models.dialog.modelId')">
            <ElInput v-model="editForm.model_id" :placeholder="$t('studio.models.placeholder.modelId')" />
          </ElFormItem>
          <ElFormItem :label="$t('studio.models.dialog.remark')">
            <ElInput v-model="editForm.extraMeta" type="textarea" :rows="2" :placeholder="$t('studio.models.placeholder.remark')" />
          </ElFormItem>
        </template>
        <ElFormItem v-else :label="$t('studio.models.dialog.meta')">
          <ElInput v-model="editForm.meta" type="textarea" :rows="3" placeholder="JSON" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="editVisible = false">{{ $t('studio.common.actions.cancel') }}</ElButton>
        <ElButton type="primary" :loading="editing" @click="submitEdit">{{ $t('studio.models.dialog.saveEdit') }}</ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  addModel,
  deleteModel,
  listModels,
  ModelCategory,
  StudioModel,
  syncCheckpointsApi,
  updateModel
} from '@/api/studio'
import './style.scss'

defineOptions({ name: 'StudioModels' })

const { t } = useI18n()

/** 四大分区（与后端 CATEGORIES 对齐） */
const categories = computed<{ key: ModelCategory; label: string }[]>(() => [
  { key: 'checkpoint', label: t('studio.models.category.checkpoint') },
  { key: 'lora', label: t('studio.models.category.lora') },
  { key: 'translate', label: t('studio.models.category.translate') },
  { key: 'matting', label: t('studio.models.category.matting') }
])

/** 类别 → i18n 键（未知类别回退显示原值） */
const CATEGORY_KEY: Record<string, string> = {
  checkpoint: 'studio.models.category.checkpoint',
  lora: 'studio.models.category.lora',
  translate: 'studio.models.category.translate',
  matting: 'studio.models.category.matting'
}

const models = ref<StudioModel[]>([])
const activeTab = ref<ModelCategory>('checkpoint')
const syncing = ref(false)
const addVisible = ref(false)
const adding = ref(false)
const editVisible = ref(false)
const editing = ref(false)

const addForm = reactive({
  category: 'checkpoint' as ModelCategory,
  name: '',
  meta: '',
  // 翻译模型结构化字段
  base_url: '',
  api_key: '',
  model_id: ''
})

const editForm = reactive({
  id: 0,
  category: 'checkpoint' as ModelCategory,
  name: '',
  meta: '',
  extraMeta: '',
  base_url: '',
  api_key: '',
  model_id: '',
  /** 编辑弹窗打开时记录的原 api_key（输入框留空则沿用） */
  originApiKey: ''
})

const isEnabled = (m: StudioModel, field: 'enabled' | 'is_default' = 'enabled') => Boolean(Number(m[field]))

const countBy = (category: ModelCategory) => models.value.filter((m) => m.category === category).length
const filteredModels = computed(() => models.value.filter((m) => m.category === activeTab.value))
const categoryText = (c: string) => {
  const key = CATEGORY_KEY[c]
  return key ? t(key) : c
}
const categoryBadge = (c: string) =>
  ({ checkpoint: 'blue', lora: 'purple', translate: 'cyan', matting: 'cyan' })[c] ?? 'blue'

/** 安全解析模型 meta（后端可能返回 JSON 字符串或对象） */
const parseMeta = (m: StudioModel): Record<string, any> => {
  if (!m.meta) return {}
  if (typeof m.meta === 'object') return m.meta as Record<string, any>
  try {
    return JSON.parse(m.meta)
  } catch {
    return {}
  }
}

/** api_key 打码：sk-abcd...wxyz */
const maskKey = (key?: string) => {
  if (!key) return t('studio.models.notSet')
  if (key.length <= 8) return '****'
  return `${key.slice(0, 4)}****${key.slice(-4)}`
}

const load = async () => {
  try {
    const res = await listModels()
    models.value = res.data ?? []
  } catch {
    ElMessage.error(t('studio.models.message.loadFailed'))
  }
}

const toggleEnabled = async (m: StudioModel, value: boolean) => {
  try {
    await updateModel(m.id, { enabled: value })
    m.enabled = value ? 1 : 0
    ElMessage.success(value ? t('studio.models.message.enabled') : t('studio.models.message.disabled'))
  } catch {
    ElMessage.error(t('studio.models.message.updateFailed'))
  }
}

const setDefault = async (m: StudioModel) => {
  try {
    await updateModel(m.id, { is_default: true })
    ElMessage.success(t('studio.models.message.setDefault', { name: m.name, category: categoryText(m.category) }))
    load()
  } catch {
    ElMessage.error(t('studio.models.message.setDefaultFailed'))
  }
}

const remove = (m: StudioModel) => {
  ElMessageBox.confirm(t('studio.models.message.deleteConfirm', { name: m.name }), t('studio.models.message.deleteTitle'), {
    type: 'warning',
    confirmButtonText: t('studio.common.actions.confirm'),
    cancelButtonText: t('studio.common.actions.cancel')
  })
    .then(async () => {
      await deleteModel(m.id)
      ElMessage.success(t('studio.models.message.deleted'))
      load()
    })
    .catch(() => undefined)
}

const openAdd = () => {
  addForm.category = activeTab.value
  addForm.name = ''
  addForm.meta = ''
  addForm.base_url = ''
  addForm.api_key = ''
  addForm.model_id = ''
  addVisible.value = true
}

/** 类别切换时清理翻译结构化字段残留 */
const onAddCategoryChange = () => {
  addForm.base_url = ''
  addForm.api_key = ''
  addForm.model_id = ''
}

/** 翻译结构化字段打包进 meta，其余字段保留在原 JSON 中 */
const buildTranslateMeta = (
  form: { base_url: string; api_key: string; model_id: string; originApiKey?: string },
  extraJson: string
) => {
  let meta: Record<string, any> = {}
  if (extraJson.trim()) {
    try {
      meta = JSON.parse(extraJson)
    } catch {
      ElMessage.warning(t('studio.models.message.remarkInvalid'))
    }
  }
  if (form.base_url.trim()) meta.base_url = form.base_url.trim()
  if (form.model_id.trim()) meta.model_id = form.model_id.trim()
  const apiKey = form.api_key.trim() || form.originApiKey || ''
  if (apiKey) meta.api_key = apiKey
  return meta
}

const submitAdd = async () => {
  if (!addForm.name.trim()) {
    ElMessage.warning(t('studio.models.message.nameRequired'))
    return
  }
  // 翻译模型前端先校验必填项，与后端 add_model 校验对齐
  if (addForm.category === 'translate') {
    if (!addForm.base_url.trim() || !addForm.model_id.trim()) {
      ElMessage.warning(t('studio.models.message.translateRequired'))
      return
    }
  }
  adding.value = true
  try {
    let meta: Record<string, any> | undefined
    if (addForm.category === 'translate') {
      meta = buildTranslateMeta(addForm, addForm.meta)
    } else if (addForm.meta.trim()) {
      try {
        meta = JSON.parse(addForm.meta)
      } catch {
        ElMessage.warning(t('studio.models.message.metaInvalid'))
      }
    }
    await addModel({ category: addForm.category, name: addForm.name.trim(), meta })
    ElMessage.success(t('studio.models.message.addSuccess'))
    addVisible.value = false
    activeTab.value = addForm.category
    load()
  } catch {
    ElMessage.error(t('studio.models.message.addFailed'))
  } finally {
    adding.value = false
  }
}

const openEdit = (m: StudioModel) => {
  const meta = parseMeta(m)
  editForm.id = m.id
  editForm.category = m.category
  editForm.name = m.name
  editForm.base_url = String(meta.base_url ?? '')
  editForm.model_id = String(meta.model_id ?? '')
  editForm.api_key = ''
  editForm.originApiKey = String(meta.api_key ?? '')
  // 翻译模型把 base_url/model_id/api_key 拆出结构化字段，剩余键作为备注 JSON
  if (m.category === 'translate') {
    const rest = { ...meta }
    delete rest.base_url
    delete rest.model_id
    delete rest.api_key
    editForm.extraMeta = Object.keys(rest).length ? JSON.stringify(rest, null, 2) : ''
    editForm.meta = ''
  } else {
    editForm.meta = m.meta && m.meta !== '{}' ? JSON.stringify(meta, null, 2) : ''
    editForm.extraMeta = ''
  }
  editVisible.value = true
}

const submitEdit = async () => {
  if (!editForm.name.trim()) {
    ElMessage.warning(t('studio.models.message.nameRequired'))
    return
  }
  editing.value = true
  try {
    let meta: Record<string, any>
    if (editForm.category === 'translate') {
      if (!editForm.base_url.trim() || !editForm.model_id.trim()) {
        ElMessage.warning(t('studio.models.message.translateRequired'))
        editing.value = false
        return
      }
      meta = buildTranslateMeta(editForm, editForm.extraMeta)
    } else {
      meta = {}
      if (editForm.meta.trim()) {
        try {
          meta = JSON.parse(editForm.meta)
        } catch {
          ElMessage.warning(t('studio.models.message.metaInvalidKeep'))
          editing.value = false
          return
        }
      }
    }
    await updateModel(editForm.id, { name: editForm.name.trim(), meta })
    ElMessage.success(t('studio.models.message.saveSuccess'))
    editVisible.value = false
    load()
  } catch {
    ElMessage.error(t('studio.models.message.saveFailed'))
  } finally {
    editing.value = false
  }
}

const syncCheckpoints = async () => {
  syncing.value = true
  try {
    await syncCheckpointsApi()
    ElMessage.success(t('studio.models.message.syncSuccess'))
    load()
  } catch {
    ElMessage.error(t('studio.models.message.syncFailed'))
  } finally {
    syncing.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
  .header-actions {
    display: flex;
    gap: 10px;
  }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 16px;
  }

  .stat-label {
    font-size: 12px;
    color: var(--art-gray-600);
    margin-bottom: 4px;
  }

  .stat-num {
    font-size: 28px;
    font-weight: 800;

    &.blue {
      color: #60a5fa;
    }

    &.cyan {
      color: #22d3ee;
    }

    &.purple {
      color: #a78bfa;
    }
  }

  .stat-sub {
    margin-top: 4px;
    font-size: 11px;
    color: var(--art-gray-500);
  }

  .tabs-row {
    display: flex;
    gap: 6px;
    margin-bottom: 14px;
  }

  .tab-item {
    padding: 7px 16px;
    font-size: 13px;
    border-radius: 6px;
    cursor: pointer;
    color: var(--art-gray-600);

    &:hover {
      color: var(--art-primary);
    }

    &.on {
      background: rgba(37, 99, 235, 0.15);
      color: var(--art-primary);
      font-weight: 600;
    }
  }

  .table-card {
    padding: 0;

    :deep(.el-table) {
      border-radius: 6px;
    }
  }

  .model-name {
    font-weight: 600;
    color: var(--art-text-gray-900);
  }

  .badge {
    display: inline-flex;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    margin-left: 6px;

    &.default {
      background: rgba(37, 99, 235, 0.15);
      color: #60a5fa;
      margin-left: 8px;
    }

    &.blue {
      background: rgba(37, 99, 235, 0.15);
      color: #60a5fa;
    }

    &.cyan {
      background: rgba(6, 182, 212, 0.15);
      color: #22d3ee;
    }

    &.purple {
      background: rgba(124, 58, 237, 0.15);
      color: #a78bfa;
    }
  }

  .meta-text {
    font-size: 11px;
    font-family: monospace;
    color: var(--art-gray-600);
    word-break: break-all;
  }

  /* 翻译模型结构化摘要：接口 / 模型 / 密钥 三行 */
  .translate-meta {
    line-height: 1.7;

    .meta-key {
      display: inline-block;
      width: 32px;
      color: var(--art-gray-500);
    }
  }

  .form-tip {
    padding: 8px 12px;
    margin: 0 0 8px 80px;
    font-size: 11px;
    line-height: 1.6;
    color: var(--art-gray-500);
    background: rgba(37, 99, 235, 0.06);
    border-radius: 6px;
  }
</style>

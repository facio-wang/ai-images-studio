<!-- 模型中心：四分区统一管理，各功能页仅引用 -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>模型中心</h1>
        <p class="desc">所有模块（生图 / 翻译 / 抠图）统一从这里管理，各功能页仅选择引用</p>
      </div>
      <div class="header-actions">
        <ElButton @click="$router.push('/manage/help')">📖 配置帮助</ElButton>
        <ElButton @click="syncCheckpoints" :loading="syncing">🔄 同步 ComfyUI 底模</ElButton>
        <ElButton type="primary" @click="openAdd">＋ 新增模型</ElButton>
      </div>
    </div>

    <!-- 统计卡 -->
    <div class="stat-grid">
      <div class="studio-card stat-card">
        <div class="stat-label">{{ categoryText(activeTab) }}数量</div>
        <div class="stat-num blue">{{ countBy(activeTab) }}</div>
        <div class="stat-sub">模型总数 {{ models.length }} · 底模 {{ countBy('checkpoint') }} · LoRA {{ countBy('lora') }} · 翻译 {{ countBy('translate') }} · 抠图 {{ countBy('matting') }}</div>
      </div>
      <div class="studio-card stat-card">
        <div class="stat-label">启用中</div>
        <div class="stat-num cyan">{{ models.filter((m) => isEnabled(m)).length }}</div>
        <div class="stat-sub">各分区默认模型各 1 个，功能页取默认执行</div>
      </div>
      <div class="studio-card stat-card">
        <div class="stat-label">ComfyUI 端点</div>
        <div class="stat-num purple" style="font-size: 16px; line-height: 40px">ComfyUI :8188</div>
        <div class="stat-sub">底模列表可从 ComfyUI 一键同步</div>
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
        <ElTableColumn prop="name" label="模型名称" min-width="180">
          <template #default="{ row }">
            <span class="model-name">{{ row.name }}</span>
            <span v-if="isEnabled(row, 'is_default')" class="badge default">默认</span>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="category" label="类别" width="110">
          <template #default="{ row }">
            <span class="badge" :class="categoryBadge(row.category)">{{ categoryText(row.category) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="meta" label="附加信息" min-width="220">
          <template #default="{ row }">
            <!-- 翻译模型：结构化摘要，api_key 打码 -->
            <template v-if="row.category === 'translate' && parseMeta(row).base_url">
              <div class="meta-text translate-meta">
                <div><span class="meta-key">接口</span>{{ parseMeta(row).base_url }}</div>
                <div><span class="meta-key">模型</span>{{ parseMeta(row).model_id || '—' }}</div>
                <div><span class="meta-key">密钥</span>{{ maskKey(parseMeta(row).api_key) }}</div>
              </div>
            </template>
            <span v-else class="meta-text">{{ row.meta && row.meta !== '{}' ? row.meta : '—' }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="启用" width="90">
          <template #default="{ row }">
            <ElSwitch :model-value="isEnabled(row)" @change="(v: any) => toggleEnabled(row, v)" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <ElButton
              size="small"
              :disabled="isEnabled(row, 'is_default')"
              @click="setDefault(row)"
            >
              设默认
            </ElButton>
            <ElButton size="small" type="primary" plain @click="openEdit(row)">编辑</ElButton>
            <ElButton size="small" type="danger" plain @click="remove(row)">删除</ElButton>
          </template>
        </ElTableColumn>
      </ElTable>
    </div>

    <!-- 新增模型 -->
    <ElDialog v-model="addVisible" title="新增模型" width="500px">
      <ElForm label-width="80px">
        <ElFormItem label="类别">
          <ElSelect v-model="addForm.category" style="width: 100%" @change="onAddCategoryChange">
            <ElOption v-for="cat in categories" :key="cat.key" :label="cat.label" :value="cat.key" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="名称">
          <ElInput v-model="addForm.name" placeholder="模型名称，如 dreamshaperXL" />
        </ElFormItem>

        <!-- 翻译模型：结构化配置（OpenAI 兼容接口） -->
        <template v-if="addForm.category === 'translate'">
          <ElFormItem label="接口地址">
            <ElInput v-model="addForm.base_url" placeholder="https://api.openai.com/v1 或兼容接口地址" />
          </ElFormItem>
          <ElFormItem label="API Key">
            <ElInput
              v-model="addForm.api_key"
              type="password"
              show-password
              placeholder="服务商控制台申请的密钥，如 sk-..."
            />
          </ElFormItem>
          <ElFormItem label="模型 ID">
            <ElInput v-model="addForm.model_id" placeholder="gpt-4o-mini / deepseek-chat 等" />
          </ElFormItem>
          <ElFormItem label="备注">
            <ElInput v-model="addForm.meta" type="textarea" :rows="2" placeholder="其他附加信息 JSON（可留空）" />
          </ElFormItem>
          <div class="form-tip">
            接口地址是提供翻译服务的 API 根地址，API Key 在服务商控制台申请（如 OpenAI 官方、硅基流动、DeepSeek 或自建中转站），
            模型 ID 是要调用的具体模型名。详见
            <ElLink type="primary" @click="$router.push('/manage/help')">帮助页</ElLink>
          </div>
        </template>

        <!-- 其他类别：自由 JSON -->
        <ElFormItem v-else label="附加信息">
          <ElInput v-model="addForm.meta" type="textarea" :rows="2" placeholder='JSON，如 {"file": "xxx.safetensors"}（可留空）' />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="addVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="adding" @click="submitAdd">确认新增</ElButton>
      </template>
    </ElDialog>

    <!-- 编辑模型 -->
    <ElDialog v-model="editVisible" :title="`编辑模型 - ${editForm.name}`" width="500px">
      <ElForm label-width="80px">
        <ElFormItem label="名称">
          <ElInput v-model="editForm.name" />
        </ElFormItem>
        <template v-if="editForm.category === 'translate'">
          <ElFormItem label="接口地址">
            <ElInput v-model="editForm.base_url" placeholder="https://api.openai.com/v1 或兼容接口地址" />
          </ElFormItem>
          <ElFormItem label="API Key">
            <ElInput v-model="editForm.api_key" type="password" show-password placeholder="留空则保持原密钥不变" />
          </ElFormItem>
          <ElFormItem label="模型 ID">
            <ElInput v-model="editForm.model_id" placeholder="gpt-4o-mini / deepseek-chat 等" />
          </ElFormItem>
          <ElFormItem label="备注">
            <ElInput v-model="editForm.extraMeta" type="textarea" :rows="2" placeholder="其他附加信息 JSON（可留空）" />
          </ElFormItem>
        </template>
        <ElFormItem v-else label="附加信息">
          <ElInput v-model="editForm.meta" type="textarea" :rows="3" placeholder="JSON" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="editVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="editing" @click="submitEdit">保存修改</ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
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

/** 四大分区（与后端 CATEGORIES 对齐） */
const categories: { key: ModelCategory; label: string }[] = [
  { key: 'checkpoint', label: '底模' },
  { key: 'lora', label: 'LoRA' },
  { key: 'translate', label: '翻译' },
  { key: 'matting', label: '抠图' }
]

const CATEGORY_TEXT: Record<string, string> = {
  checkpoint: '底模',
  lora: 'LoRA',
  translate: '翻译',
  matting: '抠图'
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
const categoryText = (c: string) => CATEGORY_TEXT[c] ?? c
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
  if (!key) return '未设置'
  if (key.length <= 8) return '****'
  return `${key.slice(0, 4)}****${key.slice(-4)}`
}

const load = async () => {
  try {
    const res = await listModels()
    models.value = res.data ?? []
  } catch {
    ElMessage.error('加载模型列表失败')
  }
}

const toggleEnabled = async (m: StudioModel, value: boolean) => {
  try {
    await updateModel(m.id, { enabled: value })
    m.enabled = value ? 1 : 0
    ElMessage.success(value ? '已启用' : '已停用')
  } catch {
    ElMessage.error('更新失败')
  }
}

const setDefault = async (m: StudioModel) => {
  try {
    await updateModel(m.id, { is_default: true })
    ElMessage.success(`已将「${m.name}」设为${categoryText(m.category)}默认`)
    load()
  } catch {
    ElMessage.error('设置默认失败')
  }
}

const remove = (m: StudioModel) => {
  ElMessageBox.confirm(`确认删除模型「${m.name}」？该操作不可恢复。`, '删除确认', { type: 'warning' })
    .then(async () => {
      await deleteModel(m.id)
      ElMessage.success('已删除')
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
      ElMessage.warning('备注不是合法 JSON，已忽略')
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
    ElMessage.warning('请输入模型名称')
    return
  }
  // 翻译模型前端先校验必填项，与后端 add_model 校验对齐
  if (addForm.category === 'translate') {
    if (!addForm.base_url.trim() || !addForm.model_id.trim()) {
      ElMessage.warning('翻译模型需要填写接口地址和模型 ID')
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
        ElMessage.warning('附加信息不是合法 JSON，已忽略')
      }
    }
    await addModel({ category: addForm.category, name: addForm.name.trim(), meta })
    ElMessage.success('新增成功')
    addVisible.value = false
    activeTab.value = addForm.category
    load()
  } catch {
    ElMessage.error('新增失败（可能与已有模型重名或缺少翻译配置）')
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
    ElMessage.warning('请输入模型名称')
    return
  }
  editing.value = true
  try {
    let meta: Record<string, any>
    if (editForm.category === 'translate') {
      if (!editForm.base_url.trim() || !editForm.model_id.trim()) {
        ElMessage.warning('翻译模型需要填写接口地址和模型 ID')
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
          ElMessage.warning('附加信息不是合法 JSON，已保持原值')
          editing.value = false
          return
        }
      }
    }
    await updateModel(editForm.id, { name: editForm.name.trim(), meta })
    ElMessage.success('已保存')
    editVisible.value = false
    load()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    editing.value = false
  }
}

const syncCheckpoints = async () => {
  syncing.value = true
  try {
    await syncCheckpointsApi()
    ElMessage.success('已触发底模同步')
    load()
  } catch {
    ElMessage.error('同步失败（ComfyUI 不可达？）')
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

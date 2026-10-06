<!-- 任务中心：任务表格（状态 tag / 耗时 / 失败重试） -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>{{ $t('studio.tasks.title') }}</h1>
        <p class="desc">{{ $t('studio.tasks.desc') }}</p>
      </div>
      <div class="header-actions">
        <ElSelect v-model="statusFilter" style="width: 130px" @change="load">
          <ElOption :label="$t('studio.tasks.allStatus')" value="" />
          <ElOption v-for="(text, key) in statusOptions" :key="key" :label="text" :value="key" />
        </ElSelect>
        <ElButton @click="load">⟳ {{ $t('studio.common.actions.refresh') }}</ElButton>
      </div>
    </div>

    <div class="studio-card table-card">
      <ElTable :data="tasks" style="width: 100%" v-loading="loading">
        <ElTableColumn prop="id" label="ID" width="70" />
        <ElTableColumn :label="$t('studio.tasks.table.type')" width="90">
          <template #default="{ row }">
            <span class="badge" :class="row.type === 'generate' ? 'blue' : 'cyan'">
              {{ typeText(row.type) }}
            </span>
          </template>
        </ElTableColumn>
        <ElTableColumn :label="$t('studio.tasks.table.status')" width="100">
          <template #default="{ row }">
            <ElTag :type="TASK_STATUS_TAG[row.status] ?? 'info'" size="small">
              {{ statusText(row.status) }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn :label="$t('studio.tasks.table.params')" min-width="220">
          <template #default="{ row }">
            <span class="params-text">{{ paramsSummary(row) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn :label="$t('studio.tasks.table.results')" width="80">
          <template #default="{ row }">
            <span>{{ resultCount(row) || '—' }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn :label="$t('studio.tasks.table.duration')" width="90">
          <template #default="{ row }">
            <span>{{ duration(row) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="retry_count" :label="$t('studio.tasks.table.retries')" width="70" />
        <ElTableColumn :label="$t('studio.tasks.table.createdAt')" width="160">
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.created_at) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn :label="$t('studio.tasks.table.actions')" width="150" fixed="right">
          <template #default="{ row }">
            <ElButton size="small" @click="showDetail(row)">{{ $t('studio.common.actions.detail') }}</ElButton>
            <!-- 失败任务可重试：手动重试会重置计数，不受自动重试上限影响 -->
            <ElTooltip
              :disabled="!isFailed(row)"
              :content="$t('studio.tasks.failTooltip', { msg: briefError(row) })"
              placement="top"
            >
              <span>
                <ElButton
                  size="small"
                  type="primary"
                  plain
                  :disabled="!isFailed(row)"
                  @click="retry(row)"
                >
                  {{ $t('studio.common.actions.retry') }}
                </ElButton>
              </span>
            </ElTooltip>
          </template>
        </ElTableColumn>
        <template #empty>
          <div class="studio-empty"><span>{{ $t('studio.tasks.empty') }}</span></div>
        </template>
      </ElTable>
    </div>

    <!-- 生成详情弹窗：完整提示词 / 模型 / 采样参数 / 产物 -->
    <GenDetailDialog v-model="detailVisible" :task="detailTask" @retry="retryDetail" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getTask, listTasks, retryTask, StudioTask } from '@/api/studio'
import { TASK_STATUS_KEY, TASK_STATUS_TAG, TASK_TYPE_KEY } from './utils'
import GenDetailDialog from './components/GenDetailDialog.vue'
import './style.scss'

defineOptions({ name: 'StudioTasks' })

const { t } = useI18n()

/** 任务类型 → 文案（未知类型回退显示原值） */
const typeText = (type: string) => {
  const key = TASK_TYPE_KEY[type]
  return key ? t(key) : type
}

/** 任务状态 → 文案（未知状态回退显示原值） */
const statusText = (status: string) => {
  const key = TASK_STATUS_KEY[status]
  return key ? t(key) : status
}

/** 状态筛选下拉（computed 保证语言切换后文案更新） */
const statusOptions = computed<Record<string, string>>(() => {
  const options: Record<string, string> = {}
  for (const [status, key] of Object.entries(TASK_STATUS_KEY)) {
    options[status] = t(key)
  }
  return options
})

const tasks = ref<StudioTask[]>([])
const loading = ref(false)
const statusFilter = ref('')
const detailVisible = ref(false)
const detailTask = ref<StudioTask | null>(null)
let refreshTimer: ReturnType<typeof setInterval> | null = null

/** 详情弹窗：重新拉一次任务保证 params/result 是最新 */
const showDetail = async (task: StudioTask) => {
  detailTask.value = task
  detailVisible.value = true
  try {
    const res = await getTask(task.id)
    if (res.data) detailTask.value = res.data
  } catch {
    // 用列表行数据兜底展示
  }
}

const retryDetail = async () => {
  if (detailTask.value) await retry(detailTask.value)
}

const load = async () => {
  loading.value = tasks.value.length === 0
  try {
    const res = await listTasks({ status: statusFilter.value || undefined, limit: 100 })
    tasks.value = res.data ?? []
  } catch {
    ElMessage.error(t('studio.tasks.loadFailed'))
  } finally {
    loading.value = false
  }
}

/** 参数摘要：prompt 截断 / 抠图模型 */
const paramsSummary = (task: StudioTask) => {
  const params = typeof task.params === 'string' ? safeParse(task.params) : task.params ?? {}
  if (task.type === 'generate') {
    return String(params.prompt ?? '').slice(0, 60) || '—'
  }
  const modelLabel = String(params.model ?? t('studio.tasks.defaultModel'))
  const assetLabel = params.asset_id ? t('studio.tasks.paramsAsset', { n: params.asset_id }) : ''
  return t('studio.tasks.paramsModel', { model: modelLabel }) + assetLabel
}

/** 产物数量 */
const resultCount = (task: StudioTask) => {
  const result = typeof task.result === 'string' ? safeParse(task.result) : task.result ?? {}
  return Array.isArray(result.asset_ids) ? result.asset_ids.length : 0
}

/** 耗时：updated_at - created_at（进行中则留空） */
const duration = (task: StudioTask) => {
  if (!task.updated_at || task.status === 'queued' || task.status === 'running') return '—'
  const ms = new Date(task.updated_at).getTime() - new Date(task.created_at).getTime()
  if (Number.isNaN(ms) || ms < 0) return '—'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

/** 是否为失败任务（仅 failed 可手动重试，手动重试不受自动重试上限限制） */
const isFailed = (task: StudioTask) => task.status === 'failed'

/** 失败原因摘要（tooltip 用，取错误首行并截断） */
const briefError = (task: StudioTask) =>
  String(task.error ?? '')
    .split('\n')[0]
    .slice(0, 80) || t('studio.tasks.unknownError')

const retry = async (task: StudioTask) => {
  if (!isFailed(task)) {
    // 非失败状态不可重试（防御：后端同样限制 queued/failed 才能重试）
    ElMessage.warning(t('studio.tasks.onlyFailedRetry'))
    return
  }
  try {
    await retryTask(task.id)
    ElMessage.success(t('studio.tasks.requeued', { n: task.id }))
    load()
  } catch {
    ElMessage.error(t('studio.tasks.retryFailed'))
  }
}

const safeParse = (value: string): Record<string, any> => {
  try {
    return JSON.parse(value)
  } catch {
    return {}
  }
}

const formatTime = (iso: string) => {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  load()
  // 进行中任务状态自动刷新
  refreshTimer = setInterval(load, 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style lang="scss" scoped>
  .header-actions {
    display: flex;
    gap: 10px;
  }

  .table-card {
    padding: 0;

    :deep(.el-table) {
      border-radius: 6px;
    }
  }

  .badge {
    display: inline-flex;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;

    &.blue {
      background: rgba(37, 99, 235, 0.15);
      color: #60a5fa;
    }

    &.cyan {
      background: rgba(6, 182, 212, 0.15);
      color: #22d3ee;
    }
  }

  .params-text,
  .time-text {
    font-size: 11px;
    color: var(--art-gray-600);
    word-break: break-all;
  }
</style>

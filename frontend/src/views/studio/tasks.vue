<!-- 任务中心：任务表格（状态 tag / 耗时 / 失败重试） -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>任务中心</h1>
        <p class="desc">生图 / 抠图任务队列与执行状态 · 失败任务可手动重试</p>
      </div>
      <div class="header-actions">
        <ElSelect v-model="statusFilter" style="width: 130px" @change="load">
          <ElOption label="全部状态" value="" />
          <ElOption v-for="(text, key) in TASK_STATUS_TEXT" :key="key" :label="text" :value="key" />
        </ElSelect>
        <ElButton @click="load">⟳ 刷新</ElButton>
      </div>
    </div>

    <div class="studio-card table-card">
      <ElTable :data="tasks" style="width: 100%" v-loading="loading">
        <ElTableColumn prop="id" label="ID" width="70" />
        <ElTableColumn label="类型" width="90">
          <template #default="{ row }">
            <span class="badge" :class="row.type === 'generate' ? 'blue' : 'cyan'">
              {{ TASK_TYPE_TEXT[row.type] || row.type }}
            </span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="状态" width="100">
          <template #default="{ row }">
            <ElTag :type="TASK_STATUS_TAG[row.status] ?? 'info'" size="small">
              {{ TASK_STATUS_TEXT[row.status] || row.status }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="参数摘要" min-width="220">
          <template #default="{ row }">
            <span class="params-text">{{ paramsSummary(row) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="产物" width="80">
          <template #default="{ row }">
            <span>{{ resultCount(row) || '—' }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="耗时" width="90">
          <template #default="{ row }">
            <span>{{ duration(row) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="retry_count" label="重试" width="70" />
        <ElTableColumn label="创建时间" width="160">
          <template #default="{ row }">
            <span class="time-text">{{ formatTime(row.created_at) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <ElButton size="small" @click="showDetail(row)">详情</ElButton>
            <!-- 失败任务可重试：手动重试会重置计数，不受自动重试上限影响 -->
            <ElTooltip
              :disabled="!isFailed(row)"
              :content="`失败原因：${briefError(row)}（点击重试重新入队）`"
              placement="top"
            >
              <span>
                <ElButton size="small" type="primary" plain :disabled="!isFailed(row)" @click="retry(row)">
                  重试
                </ElButton>
              </span>
            </ElTooltip>
          </template>
        </ElTableColumn>
        <template #empty>
          <div class="studio-empty"><span>暂无任务</span></div>
        </template>
      </ElTable>
    </div>

    <!-- 生成详情弹窗：完整提示词 / 模型 / 采样参数 / 产物 -->
    <GenDetailDialog v-model="detailVisible" :task="detailTask" @retry="retryDetail" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getTask, listTasks, retryTask, StudioTask } from '@/api/studio'
import { TASK_STATUS_TAG, TASK_STATUS_TEXT, TASK_TYPE_TEXT } from './utils'
import GenDetailDialog from './components/GenDetailDialog.vue'
import './style.scss'

defineOptions({ name: 'StudioTasks' })

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
    ElMessage.error('加载任务列表失败')
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
  return `model: ${params.model ?? '默认'}${params.asset_id ? ` · 资产 #${params.asset_id}` : ''}`
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
    .slice(0, 80) || '未知错误'

const retry = async (task: StudioTask) => {
  if (!isFailed(task)) {
    // 非失败状态不可重试（防御：后端同样限制 queued/failed 才能重试）
    ElMessage.warning('仅失败任务可重试')
    return
  }
  try {
    await retryTask(task.id)
    ElMessage.success(`任务 #${task.id} 已重新入队`)
    load()
  } catch {
    ElMessage.error('重试失败')
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

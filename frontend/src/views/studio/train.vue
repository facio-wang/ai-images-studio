<!-- LoRA 训练：数据集管理（左）+ 训练配置/监控/日志（右）；训练控制代理宿主机助手 -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>{{ $t('studio.train.title') }}</h1>
        <p class="desc">{{ $t('studio.train.desc') }}</p>
      </div>
      <ElButton :loading="envLoading" @click="loadEnv">{{ $t('studio.train.refresh') }}</ElButton>
    </div>

    <!-- 环境状态栏 -->
    <div class="studio-card env-bar" :class="envStateClass">
      <span class="env-dot" />
      <span class="env-text">{{ envStateText }}</span>
      <span v-if="envError" class="env-detail">{{ envError }}</span>
      <template v-if="env && !env.ready">
        <span class="env-label">{{ $t('studio.train.envChecks') }}</span>
        <ul class="env-items">
          <li v-for="item in env.items" :key="item.name" :class="{ bad: !item.ok }">
            <b>{{ item.name }}</b>
            <span>{{ item.detail }}</span>
          </li>
        </ul>
      </template>
    </div>

    <div class="train-layout">
      <!-- 左列：数据集 + 上传 -->
      <div class="left-col">
        <div class="studio-card">
          <div class="card-title">
            {{ $t('studio.train.datasets') }}
            <span class="count-chip">{{ datasets.length }}</span>
          </div>
          <div v-if="!datasets.length" class="studio-empty">{{ $t('studio.train.datasetEmpty') }}</div>
          <ul v-else class="dataset-list">
            <li
              v-for="ds in datasets"
              :key="ds.name"
              :class="{ active: ds.name === selected }"
              @click="selectDataset(ds.name)"
            >
              <span class="ds-name">{{ ds.name }}</span>
              <span class="ds-count">{{ ds.count }} pics</span>
              <ElButton class="ds-del" link type="danger" size="small" @click.stop="removeDataset(ds)">
                <ElIcon><Delete /></ElIcon>
              </ElButton>
            </li>
          </ul>
        </div>

        <div class="studio-card">
          <div class="card-title">{{ $t('studio.train.uploadBtn') }}</div>
          <ElUpload
            drag
            multiple
            :auto-upload="false"
            :show-file-list="false"
            accept=".png,.jpg,.jpeg,.webp,image/*"
            :on-change="onFilePicked"
          >
            <div class="upload-inner">
              <ElIcon class="upload-icon"><UploadFilled /></ElIcon>
              <div class="upload-text">{{ $t('studio.train.uploadZone') }}</div>
            </div>
          </ElUpload>
          <div class="upload-meta">
            <span>{{ $t('studio.train.nameForNew') }}</span>
            <ElInput
              v-model="newName"
              size="small"
              :placeholder="$t('studio.train.namePlaceholder')"
              maxlength="64"
              clearable
            />
          </div>
          <div class="upload-actions">
            <span class="picked-count" v-if="pickedFiles.length">+{{ pickedFiles.length }}</span>
            <ElButton type="primary" :loading="uploading" @click="doUpload">
              {{ uploading ? $t('studio.train.uploading') : $t('studio.train.uploadBtn') }}
            </ElButton>
          </div>
        </div>
      </div>

      <!-- 右列：配置 / 监控 / 日志 -->
      <div class="right-col">
        <div class="studio-card">
          <div class="card-title">{{ $t('studio.train.config') }}</div>
          <div class="config-row">
            <ElInput
              v-model="trigger"
              :placeholder="$t('studio.train.triggerPlaceholder')"
              maxlength="64"
              clearable
            />
            <ElButton
              type="primary"
              size="large"
              class="start-btn"
              :disabled="!selected"
              :loading="starting"
              @click="startTrain"
            >
              {{ $t('studio.train.startTrain') }}
            </ElButton>
          </div>
          <div v-if="!selected" class="config-hint warn">{{ $t('studio.train.noDataset') }}</div>
          <div class="config-hint">
            {{ $t('studio.train.configHint') }}
          </div>
        </div>

        <div class="studio-card">
          <div class="card-title monitor-title">
            {{ $t('studio.train.monitor') }}
            <span class="status-badge" :class="running ? 'on' : 'off'">
              {{ running ? $t('studio.train.statusRunning') : $t('studio.train.statusIdle') }}
            </span>
            <span v-if="running && status?.pid" class="pid-chip">
              {{ $t('studio.train.pidLabel') }} {{ status?.pid }}
            </span>
            <ElButton v-if="running" class="stop-btn" type="danger" size="small" @click="stopTrain">
              {{ $t('studio.train.stopTrain') }}
            </ElButton>
          </div>
          <div v-if="!running" class="studio-empty">{{ $t('studio.train.idleTip') }}</div>
          <pre v-else class="log-pre short">{{ status?.log_tail || $t('studio.train.logsEmpty') }}</pre>
        </div>

        <div class="studio-card">
          <div class="card-title monitor-title">
            {{ $t('studio.train.logs') }}
            <span v-if="logTail" class="log-meta">
              {{ $t('studio.train.logLines', { n: logLineCount }) }}
            </span>
          </div>
          <pre v-if="logTail" class="log-pre">{{ logTail }}</pre>
          <div v-else class="studio-empty">{{ $t('studio.train.logsEmpty') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, UploadFile, UploadRawFile, UploadUserFile } from 'element-plus'
import { Delete, UploadFilled } from '@element-plus/icons-vue'
import './style.scss'
import {
  LoraDataset,
  TrainEnv,
  TrainStatus,
  createLoraDataset,
  deleteLoraDataset,
  getLoraEnv,
  getLoraTrainStatus,
  listLoraDatasets,
  startLoraTrain,
  stopLoraTrain,
  uploadLoraImages
} from '@/api/lora'

defineOptions({ name: 'StudioTrain' })

const { t } = useI18n()

// ---------- 环境检测 ----------
const env = ref<TrainEnv | null>(null)
const envError = ref('')
const envLoading = ref(false)

const loadEnv = async () => {
  envLoading.value = true
  try {
    const res = await getLoraEnv()
    env.value = res.data
    envError.value = ''
  } catch {
    env.value = null
    envError.value = t('studio.train.envAgentDown')
  } finally {
    envLoading.value = false
  }
}

const envStateClass = computed(() =>
  envError.value ? 'bad' : env.value?.ready ? 'good' : 'warn'
)
const envStateText = computed(() => {
  if (envError.value) return t('studio.train.envAgentDown')
  if (!env.value) return t('studio.train.envAgentDown')
  return env.value.ready ? t('studio.train.envReady') : t('studio.train.envNotReady')
})

// ---------- 数据集 ----------
const datasets = ref<LoraDataset[]>([])
const selected = ref('')
const newName = ref('')
const pickedFiles = ref<File[]>([])
const uploading = ref(false)

const loadDatasets = async () => {
  try {
    const res = await listLoraDatasets()
    datasets.value = res.data || []
  } catch {
    // 列表加载失败保持现状（顶部拦截器已提示）
  }
}

const selectDataset = (name: string) => {
  selected.value = name
  logTail.value = ''
  running.value = false
  status.value = null
  loadStatus()
}

const onFilePicked = (file: UploadFile, files: UploadUserFile[]) => {
  const raw = file.raw
  if (!raw) return
  const ok = /\.(png|jpe?g|webp)$/i.test(raw.name)
  if (!ok) {
    ElMessage.warning(t('studio.train.uploadNone'))
    return
  }
    pickedFiles.value = files.map((f) => f.raw).filter((f): f is UploadRawFile => !!f)
}

const doUpload = async () => {
  const name = (newName.value || '').trim() || selected.value
  if (!name) {
    ElMessage.warning(t('studio.train.needName'))
    return
  }
  if (!pickedFiles.value.length) {
    ElMessage.warning(t('studio.train.uploadNone'))
    return
  }
  uploading.value = true
  try {
    // 新名字先创建（已存在则幂等），再追加上传
    const exists = datasets.value.some((d) => d.name === name)
    if (!exists) await createLoraDataset(name)
    const res = await uploadLoraImages(name, pickedFiles.value)
    ElMessage.success(t('studio.train.uploadSuccess', { n: res.data?.saved ?? 0 }))
    pickedFiles.value = []
    newName.value = ''
    await loadDatasets()
    if (selected.value !== name) selectDataset(name)
  } catch {
    // 拦截器已提示
  } finally {
    uploading.value = false
  }
}

const removeDataset = async (ds: LoraDataset) => {
  try {
    await ElMessageBox.confirm(
      t('studio.train.deleteDatasetConfirm', { name: ds.name, count: ds.count }),
      t('studio.train.deleteDataset'),
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await deleteLoraDataset(ds.name)
    ElMessage.success(t('studio.train.deleted'))
    if (selected.value === ds.name) {
      selected.value = ''
      running.value = false
      status.value = null
      logTail.value = ''
    }
    await loadDatasets()
  } catch {
    // 拦截器已提示
  }
}

// ---------- 训练控制 ----------
const trigger = ref('')
const starting = ref(false)
const running = ref(false)
const status = ref<TrainStatus | null>(null)
const logTail = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null

const logLineCount = computed(() => (logTail.value ? logTail.value.split('\n').length : 0))

const loadStatus = async () => {
  if (!selected.value) return
  try {
    const res = await getLoraTrainStatus(selected.value)
    status.value = res.data
    running.value = !!res.data?.running
    logTail.value = res.data?.log_tail || ''
    envError.value = ''
    // 训练中保持轮询刷新日志；空闲则不轮询
    if (running.value && !pollTimer) {
      pollTimer = setInterval(loadStatus, 4000)
    }
    if (!running.value && pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  } catch {
    // 助手不可达：展示错误并停止轮询，避免提示风暴
    running.value = false
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }
}

const startTrain = async () => {
  if (!selected.value) return
  const word = trigger.value.trim()
  if (!word) {
    ElMessage.warning(t('studio.train.triggerPlaceholder'))
    return
  }
  starting.value = true
  try {
    await startLoraTrain({ dataset: selected.value, trigger: word })
    ElMessage.success(t('studio.train.trainStarted'))
    await loadStatus()
  } catch {
    // 拦截器已提示（未配置助手 / 环境未就绪等）
  } finally {
    starting.value = false
  }
}

const stopTrain = async () => {
  if (!selected.value) return
  try {
    await ElMessageBox.confirm(t('studio.train.stopConfirm'), t('studio.train.stopTrain'), {
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await stopLoraTrain(selected.value)
    ElMessage.success(t('studio.train.stopSent'))
    await loadStatus()
  } catch {
    // 拦截器已提示
  }
}

onMounted(() => {
  loadEnv()
  loadDatasets()
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style lang="scss" scoped>
/* 环境状态栏 */
.env-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 16px;
  margin-bottom: 16px;
  font-size: 13px;

  .env-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #94a3b8;
  }

  &.good .env-dot {
    background: #34d399;
    box-shadow: 0 0 6px rgba(52, 211, 153, 0.8);
  }

  &.warn .env-dot {
    background: #fbbf24;
  }

  &.bad .env-dot {
    background: #f87171;
  }

  .env-label {
    margin-left: 12px;
    color: var(--art-gray-500);
    font-size: 12px;
  }

  .env-detail {
    color: var(--art-gray-500);
    font-size: 12px;
  }

  .env-items {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 16px;
    list-style: none;
    margin: 0;
    padding: 0;
    width: 100%;

    li {
      display: flex;
      gap: 6px;
      font-size: 12px;
      color: var(--art-gray-600);

      b {
        color: var(--art-primary);
        font-weight: 600;
      }

      &.bad b {
        color: #f87171;
      }
    }
  }
}

/* 双列布局：左窄右宽 */
.train-layout {
  display: grid;
  grid-template-columns: minmax(240px, 4fr) minmax(0, 8fr);
  gap: 16px;
  align-items: start;
}

.left-col,
.right-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 数据集列表 */
.count-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 6px;
  margin-left: 6px;
  border-radius: 9px;
  font-size: 11px;
  background: rgba(37, 99, 235, 0.15);
  color: #60a5fa;
}

.dataset-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 320px;
  overflow: auto;

  li {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 6px;
    cursor: pointer;
    border: 1px solid transparent;
    color: var(--art-gray-600);
    font-size: 13px;

    &:hover {
      background: rgba(37, 99, 235, 0.06);
    }

    &.active {
      background: rgba(37, 99, 235, 0.12);
      border-color: rgba(37, 99, 235, 0.4);
      color: var(--art-primary);
    }

    .ds-name {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: 600;
    }

    .ds-count {
      font-size: 11.5px;
      color: var(--art-gray-500);
    }

    .ds-del {
      opacity: 0;
    }

    &:hover .ds-del {
      opacity: 1;
    }
  }
}

/* 上传区 */
.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 18px 0;

  .upload-icon {
    font-size: 26px;
    color: var(--art-primary);
  }

  .upload-text {
    font-size: 12px;
    color: var(--art-gray-500);
  }
}

.upload-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--art-gray-500);

  .el-input {
    flex: 1;
  }
}

.upload-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;

  .picked-count {
    font-size: 12px;
    color: #60a5fa;
  }
}

/* 训练配置 */
.config-row {
  display: flex;
  gap: 10px;

  .el-input {
    flex: 1;
  }

  .start-btn {
    min-width: 128px;
  }
}

.config-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--art-gray-500);
  line-height: 1.6;

  &.warn {
    color: #fbbf24;
  }
}

/* 监控与日志 */
.monitor-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;

  &.on {
    background: rgba(52, 211, 153, 0.15);
    color: #34d399;
  }

  &.off {
    background: var(--art-gray-200);
    color: var(--art-gray-500);
  }
}

.pid-chip {
  font-size: 11.5px;
  color: var(--art-gray-500);
}

.stop-btn {
  margin-left: auto;
}

.log-meta {
  font-size: 11.5px;
  font-weight: 400;
  color: var(--art-gray-500);
}

.log-pre {
  margin: 0;
  padding: 12px;
  max-height: 320px;
  overflow: auto;
  border-radius: 6px;
  background: rgba(2, 6, 23, 0.55);
  border: 1px solid var(--art-border-dashed-color);
  color: #93c5fd;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-all;

  &.short {
    max-height: 200px;
  }
}

@media (max-width: 900px) {
  .train-layout {
    grid-template-columns: 1fr;
  }
}
</style>

<!-- 生图工作台：左侧参数表单 + 右侧结果网格 + 底部历史 -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>生图</h1>
        <p class="desc">提交 ComfyUI 文生图任务 · 模型来自「模型中心」已启用的底模</p>
      </div>
      <ElButton @click="$router.push('/manage/models')">模型中心 →</ElButton>
    </div>

    <div class="gen-layout">
      <!-- 左参数面板 -->
      <div class="gen-side">
        <div class="studio-card">
          <div class="card-title">提示词</div>
          <ElInput
            v-model="form.prompt"
            type="textarea"
            :rows="5"
            placeholder="描述你想画的画面，例如：赛博朋克风格的城市夜景，霓虹灯，雨后街道…"
          />

          <div class="card-title" style="margin-top: 16px">基础模型</div>
          <ElSelect v-model="form.checkpoint" placeholder="默认底模" style="width: 100%" @change="onCheckpointChange">
            <ElOption
              v-for="m in checkpointOptions"
              :key="m.id"
              :label="modelLabel(m)"
              :value="m.name"
            />
          </ElSelect>
          <div v-if="isZImage" class="model-hint zimage">
            🈶 Z-Image 原生支持中文：提示词直出、<b>无需配置翻译模型</b>；采样自动固定 8步 · CFG 1（res_multistep）
          </div>
          <div v-else-if="form.checkpoint" class="model-hint">
            SDXL 系底模：中文提示词将自动翻译/增强为英文后发送（需在模型中心配置翻译模型）
          </div>

          <div class="card-title" style="margin-top: 16px">分辨率</div>
          <div class="size-grid">
            <div
              v-for="preset in sizePresets"
              :key="preset.label"
              class="size-item"
              :class="{ on: form.width === preset.w && form.height === preset.h }"
              @click="
                () => {
                  form.width = preset.w
                  form.height = preset.h
                }
              "
            >
              {{ preset.label }}
            </div>
          </div>

          <div class="card-title" style="margin-top: 16px">采样参数</div>
          <div class="param-row">
            <span>Steps</span>
            <ElSlider v-model="form.steps" :min="1" :max="60" style="width: 140px" />
            <b>{{ form.steps }}</b>
          </div>
          <div class="param-row">
            <span>CFG</span>
            <ElSlider v-model="form.cfg" :min="1" :max="20" :step="0.5" style="width: 140px" />
            <b>{{ form.cfg }}</b>
          </div>
          <div class="param-row seed">
            <span>Seed</span>
            <ElInput v-model="form.seed" style="width: 130px" placeholder="-1 随机" />
            <ElButton @click="randomSeed">🎲</ElButton>
          </div>

          <div class="param-row" style="margin-top: 10px">
            <span>生成数量</span>
            <ElInputNumber v-model="form.count" :min="1" :max="8" />
          </div>

          <!-- 海报文字叠加：AI 底模画不出可读文字，用真实字体渲染中英文 -->
          <ElCollapse class="text-collapse">
            <ElCollapseItem name="texts">
              <template #title>
                <span class="card-title" style="margin: 0">添加文字（海报文字叠加）</span>
              </template>
              <div v-for="(t, i) in textItems" :key="i" class="text-item">
                <div class="text-item-head">
                  <span>文字 #{{ i + 1 }}</span>
                  <ElButton size="small" text type="danger" @click="removeText(i)">删除</ElButton>
                </div>
                <ElInput
                  v-model="t.content"
                  type="textarea"
                  :rows="2"
                  placeholder="文字内容，支持中英文，换行用回车"
                />
                <div class="text-grid">
                  <label>字号<ElInputNumber v-model="t.size" :min="8" :max="400" size="small" /></label>
                  <label>颜色<ElColorPicker v-model="t.color" size="small" /></label>
                  <label>X<ElInput v-model="t.x" size="small" placeholder="像素或 50%" /></label>
                  <label>Y<ElInput v-model="t.y" size="small" placeholder="像素或 50%" /></label>
                  <label>
                    对齐
                    <ElSelect v-model="t.align" size="small">
                      <ElOption label="左" value="left" />
                      <ElOption label="中" value="center" />
                      <ElOption label="右" value="right" />
                    </ElSelect>
                  </label>
                  <label class="check-label">
                    <ElCheckbox v-model="t.bold" size="small">粗体</ElCheckbox>
                  </label>
                  <label class="check-label">
                    <ElCheckbox v-model="t.useBg" size="small">背景衬条</ElCheckbox>
                  </label>
                  <label v-if="t.useBg">
                    衬条色<ElColorPicker v-model="t.bgColor" size="small" />
                  </label>
                </div>
              </div>
              <div class="text-actions">
                <ElButton size="small" @click="addText">+ 添加文字</ElButton>
                <ElButton size="small" :loading="previewing" @click="previewTexts">👁 预览</ElButton>
              </div>
              <div v-if="previewUrl" class="text-preview">
                <img :src="previewUrl" alt="文字预览" />
              </div>
            </ElCollapseItem>
          </ElCollapse>
        </div>

        <ElButton
          type="primary"
          class="submit-btn"
          :loading="submitting"
          :disabled="!form.prompt.trim()"
          @click="submit"
        >
          🚀 提交生成任务
        </ElButton>
      </div>

      <!-- 右结果区 -->
      <div class="gen-main">
        <div class="studio-card">
          <div class="card-title">
            结果画布
            <span v-if="taskInfo" class="result-meta">任务 #{{ taskInfo.id }} · {{ TASK_STATUS_TEXT[taskInfo.status] }}</span>
          </div>

          <div v-if="submitting || polling" class="gen-waiting">
            <TaskProgress
              :percent="waitPercent"
              :elapsed-sec="waitElapsed"
              :phase-text="waitPhase"
              hint="生图速度取决于 ComfyUI 侧显卡性能，低配显卡可能需要几分钟"
            />
          </div>

          <div v-else-if="results.length" class="result-grid">
            <div v-for="asset in results" :key="asset.id" class="studio-thumb result-item">
              <ElImage
                :src="asset.url"
                :preview-src-list="results.map((r) => r.url)"
                :initial-index="results.findIndex((r) => r.id === asset.id)"
                preview-teleported
                :alt="asset.labels || ''"
                fit="cover"
                class="thumb-img"
              />
              <div class="thumb-ops">
                <ElButton size="small" tag="a" :href="asset.url" target="_blank">⬇</ElButton>
                <ElButton size="small" @click="goMatting(asset.id)">✂ 抠图</ElButton>
              </div>
            </div>
          </div>

          <div v-else class="studio-empty"><span>提交任务后，生成结果将展示在这里</span></div>
        </div>

        <!-- 底部历史 -->
        <div class="studio-card">
          <div class="card-title">生成历史</div>
          <div v-if="history.length" class="history-row">
            <div v-for="asset in history" :key="asset.id" class="history-item">
              <div class="studio-thumb history-thumb">
                <ElImage
                  :src="asset.thumb_url"
                  :preview-src-list="[asset.url]"
                  preview-teleported
                  fit="cover"
                  class="thumb-img"
                />
              </div>
              <span class="history-label">{{ formatTime(asset.created_at) }}</span>
            </div>
          </div>
          <div v-else class="studio-empty"><span>暂无生成记录</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getAsset,
  getTask,
  listModels,
  PosterTextItem,
  previewPosterTexts,
  StudioAsset,
  StudioModel,
  StudioTask,
  submitGenerate,
  taskAssetIds
} from '@/api/studio'
import { fetchRecentAssets, TASK_STATUS_TEXT } from './utils'
import TaskProgress from './components/TaskProgress.vue'
import './style.scss'

defineOptions({ name: 'StudioGenerate' })

const router = useRouter()

const form = reactive({
  prompt: '',
  checkpoint: '',
  width: 1024,
  height: 1024,
  steps: 20,
  cfg: 7,
  seed: '-1',
  count: 1
})

/** 尺寸预设（对齐设计稿常用比例） */
const sizePresets = [
  { label: '1024×1024', w: 1024, h: 1024 },
  { label: '768×1344', w: 768, h: 1344 },
  { label: '1344×768', w: 1344, h: 768 },
  { label: '768×1152', w: 768, h: 1152 },
  { label: '1152×768', w: 1152, h: 768 },
  { label: '512×512', w: 512, h: 512 }
]

const checkpointOptions = ref<StudioModel[]>([])
const results = ref<StudioAsset[]>([])
const history = ref<StudioAsset[]>([])
const taskInfo = ref<StudioTask | null>(null)
const submitting = ref(false)
const polling = ref(false)
/** 等待进度状态：目标百分比 / 已等待秒数 / 阶段文案 */
const waitPercent = ref(4)
const waitElapsed = ref(0)
const waitPhase = ref('正在提交…')
const waitTimer = setInterval(() => {
  if (submitting.value || polling.value) waitElapsed.value++
}, 1000)
onUnmounted(() => clearInterval(waitTimer))

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

/** 工作流类型：meta.model_type 优先，名称含 z_image/zimage 兜底（与后端 infer_model_type 对齐） */
const modelType = (m: StudioModel): string => {
  const meta = parseMeta(m)
  if (meta.model_type) return String(meta.model_type)
  const name = (m.name || '').toLowerCase()
  return name.includes('z_image') || name.includes('zimage') ? 'z_image' : 'checkpoint'
}

const isZImage = computed(
  () => modelType(checkpointOptions.value.find((m) => m.name === form.checkpoint) ?? ({} as StudioModel)) === 'z_image'
)

const modelLabel = (m: StudioModel) => {
  const parts = [m.name]
  if (Number(m.is_default)) parts.push('（默认）')
  if (modelType(m) === 'z_image') parts.push(' 🈶中文直出')
  return parts.join('')
}

/** 切换底模时按类型自适应采样参数：Z-Image 固定 8步/cfg1，SDXL 系回默认 20步/cfg7 */
const onCheckpointChange = (name: string) => {
  const model = checkpointOptions.value.find((m) => m.name === name)
  if (modelType(model ?? ({} as StudioModel)) === 'z_image') {
    form.steps = 8
    form.cfg = 1
  } else {
    form.steps = 20
    form.cfg = 7
  }
}

let pollTimer: ReturnType<typeof setTimeout> | null = null

/** 拉取启用的底模（category=checkpoint），默认选中 is_default */
const loadCheckpoints = async () => {
  try {
    const res = await listModels('checkpoint')
    checkpointOptions.value = (res.data ?? []).filter((m) => Boolean(Number(m.enabled)))
    const def = checkpointOptions.value.find((m) => Boolean(Number(m.is_default)))
    if (def) {
      form.checkpoint = def.name
      onCheckpointChange(def.name)
    }
  } catch {
    ElMessage.error('加载模型列表失败')
  }
}

const loadHistory = async () => {
  try {
    history.value = await fetchRecentAssets('generate', 12)
  } catch {
    // 历史拉取失败不阻塞生图主流程
  }
}

const randomSeed = () => {
  form.seed = String(Math.floor(Math.random() * 2147483647))
}

// ---------- 海报文字叠加 ----------

/** 单个文字元素的本地编辑状态（useBg/bgColor 仅前端用，提交时合成 bg） */
interface TextItemEdit {
  content: string
  x: string
  y: string
  size: number
  color: string
  align: 'left' | 'center' | 'right'
  bold: boolean
  useBg: boolean
  bgColor: string
}

const emptyText = (): TextItemEdit => ({
  content: '',
  x: '50%',
  y: '50%',
  size: 48,
  color: '#FFFFFF',
  align: 'center',
  bold: true,
  useBg: false,
  bgColor: '#000000CC'
})

const textItems = ref<TextItemEdit[]>([])
const previewing = ref(false)
const previewUrl = ref('')

const addText = () => textItems.value.push(emptyText())
const removeText = (i: number) => {
  textItems.value.splice(i, 1)
  previewUrl.value = ''
}

/** 把编辑状态转换为后端 texts 配置（过滤空内容） */
const buildTextsPayload = (): PosterTextItem[] =>
  textItems.value
    .filter((t) => t.content.trim())
    .map((t) => ({
      content: t.content,
      x: t.x || 0,
      y: t.y || 0,
      size: t.size,
      color: t.color,
      align: t.align,
      bold: t.bold,
      bg: t.useBg ? t.bgColor : null
    }))

/** 预览：用一张程序生成的占位底图调 /api/poster/preview */
const previewTexts = async () => {
  const texts = buildTextsPayload()
  if (!texts.length) {
    ElMessage.warning('请先填写至少一条文字内容')
    return
  }
  previewing.value = true
  try {
    // 占位底图：按当前分辨率画一张带渐变感的纯色图
    const canvas = document.createElement('canvas')
    canvas.width = form.width
    canvas.height = form.height
    const ctx = canvas.getContext('2d')!
    ctx.fillStyle = '#3b4252'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    const blob: Blob = await new Promise((resolve) =>
      canvas.toBlob((b) => resolve(b as Blob), 'image/png')
    )
    const res = await previewPosterTexts(blob, texts)
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = URL.createObjectURL(res)
  } catch {
    ElMessage.error('文字预览失败')
  } finally {
    previewing.value = false
  }
}

/** 提交任务并轮询，done 后按 asset_ids 拉产物 + 刷新历史 */
const submit = async () => {
  const prompt = form.prompt.trim()
  if (!prompt) return
  submitting.value = true
  results.value = []
  waitPercent.value = 4
  waitElapsed.value = 0
  waitPhase.value = '正在提交…'
  try {
    const res = await submitGenerate({
      prompt,
      checkpoint: form.checkpoint || undefined,
      width: form.width,
      height: form.height,
      steps: form.steps,
      cfg: form.cfg,
      seed: Number(form.seed) || -1,
      count: form.count,
      // 海报文字叠加：有内容时随任务提交，生图完成后由后端渲染真实文字
      ...(buildTextsPayload().length ? { texts: buildTextsPayload() } : {})
    })
    taskInfo.value = res.data
    await poll(res.data.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '提交任务失败')
  } finally {
    submitting.value = false
  }
}

/**
 * 轮询循环：每 2s 查一次任务状态（瞬断自动重试），上限 15 分钟
 * （生图速度取决于 ComfyUI 侧硬件：低配显卡 + 大参数可能远超默认超时）
 */
const poll = (taskId: number) =>
  new Promise<void>((resolve, reject) => {
    polling.value = true
    waitPhase.value = '排队等待 GPU…'
    waitPercent.value = 10
    let startedAt = 0
    let fails = 0
    const tick = async () => {
      try {
        const res = await getTask(taskId)
        const task = res.data
        fails = 0
        taskInfo.value = task
        if (task.status === 'running' && !startedAt) startedAt = Date.now()
        if (task.status === 'queued') {
          waitPhase.value = '排队等待 GPU…'
          waitPercent.value = Math.max(waitPercent.value, 10)
        } else if (task.status === 'running') {
          const runSec = startedAt ? Math.round((Date.now() - startedAt) / 1000) : 0
          waitPhase.value = '正在生成，请稍候…'
          waitPercent.value = Math.min(95, Math.max(waitPercent.value, 15 + runSec * 1.2))
        }
        if (task.status === 'done') {
          polling.value = false
          await loadResults(taskAssetIds(task))
          loadHistory()
          resolve()
          return
        }
        if (task.status === 'failed') {
          polling.value = false
          reject(new Error(task.error || '任务执行失败'))
          return
        }
        pollTimer = setTimeout(tick, 2000)
      } catch {
        // 网络抖动/后端繁忙：退避重试，连续 10 次失败才判定失联，不中断等待
        fails++
        if (fails >= 10 || Date.now() - (submitStartedAt || Date.now()) > 900000) {
          polling.value = false
          reject(new Error('任务状态查询连续失败，请稍后在任务中心查看结果'))
          return
        }
        pollTimer = setTimeout(tick, Math.min(2000 * fails, 8000))
      }
    }
    submitStartedAt = Date.now()
    tick()
  })

let submitStartedAt = 0

const loadResults = async (ids: number[]) => {
  const list: StudioAsset[] = []
  for (const id of ids) {
    try {
      const res = await getAsset(id)
      if (res.data) list.push(res.data)
    } catch {
      // 单个产物拉取失败不影响整体
    }
  }
  results.value = list
}

const formatTime = (iso: string) =>
  new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })

const goMatting = (assetId: number) => {
  router.push({ path: '/studio/matting', query: { asset_id: String(assetId) } })
}

onMounted(() => {
  loadCheckpoints()
  loadHistory()
})
</script>

<style lang="scss" scoped>
  .gen-layout {
    display: grid;
    grid-template-columns: minmax(280px, 4fr) minmax(0, 8fr);
    gap: 16px;
    align-items: start;
  }

  .gen-side {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .size-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
  }

  .size-item {
    padding: 6px 0;
    text-align: center;
    font-size: 11px;
    border-radius: 6px;
    border: 1px solid var(--art-border-dashed-color);
    color: var(--art-gray-600);
    cursor: pointer;

    &:hover {
      border-color: var(--art-primary);
      color: var(--art-primary);
    }

    &.on {
      background: rgba(37, 99, 235, 0.15);
      border-color: rgba(37, 99, 235, 0.4);
      color: var(--art-primary);
      font-weight: 600;
    }
  }

  .param-row {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    color: var(--art-gray-600);
    margin-bottom: 8px;

    b {
      color: var(--art-text-gray-900);
      min-width: 28px;
    }

    &.seed {
      .el-button {
        padding: 5px 10px;
      }
    }
  }

  .model-hint {
    margin-top: 8px;
    padding: 7px 10px;
    font-size: 11px;
    line-height: 1.6;
    color: var(--art-gray-500);
    background: rgba(37, 99, 235, 0.06);
    border-radius: 6px;

    &.zimage {
      color: #0e7490;
      background: rgba(6, 182, 212, 0.1);

      b {
        color: #0891b2;
      }
    }
  }

  /* ElImage 铺满缩略容器（结果网格/历史条共用） */
  .thumb-img {
    width: 100%;
    height: 100%;
    cursor: zoom-in;

    :deep(img) {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  .submit-btn {
    width: 100%;
    height: 42px;
    font-size: 14px;
  }

  /* ---------- 海报文字叠加 ---------- */

  .text-collapse {
    margin-top: 16px;
    border: none;

    :deep(.el-collapse-item__header) {
      height: auto;
      border: none;
    }

    :deep(.el-collapse-item__wrap) {
      border: none;
    }
  }

  .text-item {
    padding: 10px;
    margin-bottom: 10px;
    border: 1px dashed var(--art-border-dashed-color);
    border-radius: 8px;
  }

  .text-item-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    font-size: 12px;
    color: var(--art-gray-600);
  }

  .text-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px 10px;
    margin-top: 8px;

    label {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      color: var(--art-gray-600);

      .el-input-number,
      .el-select {
        flex: 1;
        width: 100%;
      }
    }

    .check-label {
      justify-content: flex-start;
    }
  }

  .text-actions {
    display: flex;
    gap: 8px;
  }

  .text-preview {
    margin-top: 10px;
    text-align: center;

    img {
      max-width: 100%;
      border-radius: 6px;
      border: 1px solid var(--art-border-dashed-color);
    }
  }

  .result-meta {
    font-weight: 400;
    font-size: 11px;
    color: var(--art-gray-500);
    margin-left: 8px;
  }

  .gen-waiting {
    padding: 40px 20px;
  }

  .result-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
  }

  .result-item {
    aspect-ratio: 1;
    border-radius: 6px;
  }

  .history-row {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .history-item {
    flex-shrink: 0;
    text-align: center;
  }

  .history-thumb {
    width: 80px;
    height: 80px;
    border-radius: 6px;
  }

  .history-label {
    display: block;
    font-size: 10px;
    color: var(--art-gray-500);
    margin-top: 4px;
  }
</style>

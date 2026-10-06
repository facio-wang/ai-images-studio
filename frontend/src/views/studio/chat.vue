<!-- 对话工作台：左侧会话栏（缩略图/时间/删除）+ 消息流（图片点击预览、内嵌生成参数面板）+ 输入区（高级参数） -->
<template>
  <div class="studio-page chat-page">
    <!-- 生图服务未启动横幅，附一键启动入口 -->
    <ElAlert
      v-if="serviceDown"
      type="warning"
      :closable="false"
      show-icon
      :title="$t('studio.common.service.chatBannerTitle')"
      style="margin-bottom: 14px"
    >
      <template #default>
        <div class="alert-ops">
          <span>{{ $t('studio.common.service.chatBannerDesc') }}</span>
          <ElButton size="small" type="warning" plain :loading="starting" @click="startService">
            {{ starting ? $t('studio.common.service.startingBtn', { n: startElapsed }) : $t('studio.common.service.startBtn') }}
          </ElButton>
        </div>
      </template>
    </ElAlert>

    <div class="chat-layout">
      <!-- 左侧会话栏 -->
      <div class="chat-side">
        <ElButton type="primary" class="new-session-btn" @click="newSession">
          ＋ {{ $t('studio.chat.newSession') }}
        </ElButton>
        <div class="session-list">
          <div
            v-for="s in sessions"
            :key="s.id"
            class="session-item"
            :class="{ on: s.id === sessionId }"
            @click="switchSession(s.id)"
          >
            <div class="session-thumb" :class="{ checker: false }">
              <img v-if="s.thumb" :src="s.thumb" loading="lazy" />
              <span v-else class="session-thumb-empty">💬</span>
            </div>
            <div class="session-meta">
              <span class="session-title truncate">{{ s.title }}</span>
              <span class="session-time">{{ formatSessionTime(s.created_at) }}</span>
            </div>
            <span
              class="session-del"
              :title="$t('studio.chat.deleteSession')"
              @click.stop="removeSession(s.id)"
              >×</span
            >
          </div>
          <div v-if="!sessions.length" class="studio-empty"><span>{{ $t('studio.chat.noSessions') }}</span></div>
        </div>
      </div>

      <!-- 主区：会话头 + 消息流 + 输入区 -->
      <div class="chat-main">
        <div class="chat-head">
          <span class="chat-head-title truncate">{{ currentTitle }}</span>
          <span class="chat-head-stats">
            {{ $t('studio.chat.msgCount', { n: messages.length }) }} ·
            {{ $t('studio.chat.imgCount', { n: totalImgCount }) }}
          </span>
        </div>

        <div ref="flowRef" class="chat-flow">
          <div v-for="msg in messages" :key="msg.id" class="chat-msg" :class="{ rev: msg.role === 'user' }">
            <div class="chat-ava" :class="msg.role">{{ msg.role === 'user' ? $t('studio.chat.avaMe') : 'AI' }}</div>
            <div class="chat-bubble">
              <div class="msg-text">{{ msg.content }}</div>
              <!-- 消息内嵌产物图：点击打开预览，AI 图下方挂生成参数面板 -->
              <div v-if="msg.assetList.length" class="msg-imgs">
                <div
                  v-for="asset in msg.assetList"
                  :key="asset.id"
                  class="chat-img"
                  :class="{ checker: asset.type === 'matting' }"
                >
                  <img
                    :src="asset.url"
                    :alt="asset.labels || asset.filename || $t('studio.chat.assetAlt', { n: asset.id })"
                    @click="openPreview(asset, msg)"
                  />
                  <!-- 生成参数折叠面板（仅 AI 生图消息） -->
                  <div v-if="msg.task && snapOf(msg)" class="gen-params">
                    <div class="gp-head" @click="toggleParams(msg.id)">
                      <span>⚙ {{ $t('studio.chat.paramPanel') }}</span>
                      <i class="gp-arrow" :class="{ open: paramOpen[msg.id] }">▾</i>
                    </div>
                    <div v-show="paramOpen[msg.id]" class="gp-body">
                      <div class="gp-row">
                        <span class="k">Prompt</span>
                        <span class="v">{{ snapOf(msg)!.prompt }}</span>
                      </div>
                      <div v-if="snapOf(msg)!.negative" class="gp-row">
                        <span class="k">Negative</span>
                        <span class="v">{{ snapOf(msg)!.negative }}</span>
                      </div>
                      <div class="gp-row">
                        <span class="k">Seed</span>
                        <span class="v">{{ regenDraft[msg.id]?.seed ?? snapOf(msg)!.seed ?? -1 }}</span>
                      </div>
                      <div class="gp-row">
                        <span class="k">{{ $t('studio.chat.sizeLabel') }}</span>
                        <span class="v">{{ sizeText(draftOf(msg)) }}</span>
                      </div>
                      <div class="gp-row">
                        <span class="k">{{ $t('studio.chat.stepsLabel') }}</span>
                        <span class="v">{{ snapOf(msg)!.steps }} · CFG {{ snapOf(msg)!.cfg }}</span>
                      </div>
                      <!-- 手动改参重新生成 -->
                      <div class="gp-regen">
                        <div class="gp-regen-tip">{{ $t('studio.chat.regenHint') }}</div>
                        <div class="gp-regen-seed">
                          <ElInput
                            v-model="regenDraft[msg.id]!.seed"
                            size="small"
                            :placeholder="String(snapOf(msg)!.seed ?? -1)"
                          />
                          <ElButton size="small" :title="$t('studio.chat.random')" @click="randomSeed(msg.id)">🎲</ElButton>
                        </div>
                        <div class="ratio-chips">
                          <span
                            v-for="p in SIZE_PRESETS"
                            :key="p.ratio"
                            class="ratio-chip"
                            :class="{ on: draftOf(msg).width === p.w && draftOf(msg).height === p.h }"
                            @click="applyRatio(msg.id, p)"
                            >{{ p.ratio }}</span
                          >
                        </div>
                        <ElButton type="primary" plain class="gp-regen-btn" @click="regenerateWith(msg)">
                          {{ $t('studio.chat.withParams') }}
                        </ElButton>
                      </div>
                      <div class="gp-ops">
                        <span @click="regenerateWith(msg)">⟳ {{ $t('studio.chat.regen') }}</span>
                        <span @click="copyParams(msg)">⧉ {{ $t('studio.chat.copyParams') }}</span>
                        <span @click="openPreview(asset, msg)">🔍 {{ $t('studio.chat.expand') }}</span>
                        <a :href="asset.url" :download="asset.filename || 'image.png'">
                          ⬇ {{ $t('studio.common.actions.download') }}
                        </a>
                        <span @click="viewAsset(asset)">{{ $t('studio.common.actions.detail') }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <span class="time">{{ formatTime(msg.created_at) }}</span>
              <div v-if="msg.task_id && taskFailed[msg.task_id]" class="task-retry-row">
                <ElButton size="small" type="warning" plain :loading="retryingTaskId === msg.task_id" @click="retryMsgTask(msg)">
                  {{ $t('studio.chat.retryTask', { n: msg.task_id }) }}
                </ElButton>
              </div>
            </div>
          </div>

          <div v-if="waitingTask" class="chat-msg">
            <div class="chat-ava ai">AI</div>
            <div class="chat-bubble">
              <div class="msg-text">{{ $t('studio.chat.taskWaiting', { n: waitingTask }) }}</div>
              <ElIcon class="is-loading spin"><Loading /></ElIcon>
            </div>
          </div>

          <div v-if="!messages.length && !waitingTask" class="studio-empty">
            <span>{{ $t('studio.chat.emptyHint') }}</span>
          </div>
        </div>

        <!-- 高级参数折叠 -->
        <div class="advanced-bar">
          <span class="adv-toggle" @click="advancedOpen = !advancedOpen">
            ⚙ {{ $t('studio.chat.advanced') }} <i :class="{ open: advancedOpen }">▾</i>
          </span>
          <span class="adv-model">{{ $t('studio.chat.localInference') }}<template v-if="defaultModel"> · {{ defaultModel }}</template></span>
          <span class="adv-clear" @click="clearHistory">{{ $t('studio.chat.clearHistory') }}</span>
        </div>
        <div v-show="advancedOpen" class="advanced-panel">
          <div class="adv-row">
            <span class="k">{{ $t('studio.chat.negative') }}</span>
            <ElInput v-model="advanced.negative" type="textarea" :rows="2" resize="none" placeholder="worst quality, low quality..." />
          </div>
          <div class="adv-row">
            <span class="k">{{ $t('studio.chat.size') }}</span>
            <div class="ratio-chips">
              <span
                v-for="p in SIZE_PRESETS"
                :key="p.ratio"
                class="ratio-chip"
                :class="{ on: advanced.width === p.w && advanced.height === p.h }"
                @click="advanced.width = p.w; advanced.height = p.h"
                >{{ p.ratio }}</span
              >
            </div>
          </div>
          <div class="adv-row three">
            <span class="k">{{ $t('studio.chat.stepsLabel') }}</span>
            <ElInputNumber v-model="advanced.steps" :min="1" :max="50" size="small" />
            <span class="k">CFG</span>
            <ElInputNumber v-model="advanced.cfg" :min="1" :max="20" :step="0.5" size="small" />
            <span class="k">Seed</span>
            <ElInput v-model="advanced.seed" size="small" style="width: 120px" />
          </div>
        </div>

        <!-- 底部输入区 -->
        <div class="chat-input">
          <div class="chips">
            <span v-for="cmd in quickCommands" :key="cmd.label" class="quick-chip" @click="send(cmd.text)">
              {{ cmd.label }}
            </span>
          </div>
          <div class="input-row">
            <ElTooltip :content="$t('studio.chat.attachTip')" placement="top">
              <span class="attach-btn" @click="attachHint">📎</span>
            </ElTooltip>
            <ElInput
              v-model="input"
              type="textarea"
              :rows="2"
              resize="none"
              :placeholder="$t('studio.chat.inputPlaceholder')"
              @keydown.enter.exact.prevent="send()"
            />
            <ElButton type="primary" class="send-btn" :loading="sending" @click="send()">➤</ElButton>
          </div>
        </div>
      </div>
    </div>

    <!-- 大图预览：左图右参数（重新生成/复制参数/下载/作为参考图） -->
    <ElDialog v-model="preview.visible" width="min(1180px, 94vw)" :show-close="false" align-center class="preview-dialog">
      <div v-if="preview.asset" class="preview-wrap">
        <div class="preview-img" :class="{ checker: preview.asset.type === 'matting' }">
          <img :src="preview.asset.url" :alt="preview.asset.labels || ''" />
        </div>
        <div class="preview-side">
          <div class="pv-title">
            {{ $t('studio.chat.previewTitle') }}
            <span v-if="preview.snap" class="size-tag">{{ preview.snap.width }} × {{ preview.snap.height }}</span>
          </div>
          <template v-if="preview.snap">
            <div class="pv-k">{{ $t('studio.chat.promptLabel') }}</div>
            <div class="pv-v">{{ preview.snap.prompt }}</div>
            <div class="pv-k">Negative</div>
            <div class="pv-v">{{ preview.snap.negative || '—' }}</div>
            <div class="pv-k">Seed</div>
            <div class="pv-v">{{ preview.snap.seed ?? -1 }}</div>
            <div class="pv-k">{{ $t('studio.chat.sizeLabel') }}</div>
            <div class="pv-v">{{ sizeText(preview.snap) }}</div>
            <div class="pv-k">{{ $t('studio.chat.stepsLabel') }}</div>
            <div class="pv-v">{{ preview.snap.steps }} · CFG {{ preview.snap.cfg }}</div>
          </template>
          <div class="pv-ops">
            <a class="pv-btn" :href="preview.asset.url" :download="preview.asset.filename || 'image.png'">
              ⬇ {{ $t('studio.common.actions.download') }}
            </a>
            <span class="pv-btn" @click="copyParams(preview.msg!)">⧉ {{ $t('studio.chat.copyParams') }}</span>
            <span class="pv-btn" @click="regenerateWith(preview.msg!)">
              ⟳ {{ $t('studio.chat.regen') }}
            </span>
            <ElTooltip :content="$t('studio.chat.asRefTip')" placement="top">
              <span class="pv-btn disabled">📎 {{ $t('studio.chat.asRef') }}</span>
            </ElTooltip>
          </div>
        </div>
      </div>
    </ElDialog>

    <!-- 生成详情弹窗：完整提示词 / 模型 / 参数 -->
    <GenDetailDialog v-model="detailVisible" :asset="detailAsset" />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import {
  ChatMessage,
  ChatSession,
  QuickCommand,
  StudioAsset,
  StudioModel,
  StudioTask,
  deleteChatSession,
  fetchAssetsByIds,
  getAsset,
  getQuickCommands,
  getTask,
  listChatMessages,
  listChatSessions,
  listModels,
  parseMaybeJson,
  pollTask,
  retryTask,
  sendChat,
  taskAssetIds
} from '@/api/studio'
import { storeToRefs } from 'pinia'
import { useSystemStatusStore } from '@/store/modules/systemStatus'
import GenDetailDialog from './components/GenDetailDialog.vue'
import './style.scss'

defineOptions({ name: 'StudioChat' })

const { t } = useI18n()

interface ChatViewMessage extends ChatMessage {
  assetList: StudioAsset[]
  /** 关联任务（生成参数面板数据源） */
  task?: StudioTask
}

/** 比例预设（与生图页保持一致的 SDXL 常用尺寸） */
const SIZE_PRESETS = [
  { ratio: '1:1', w: 1024, h: 1024 },
  { ratio: '3:4', w: 832, h: 1216 },
  { ratio: '4:3', w: 1216, h: 832 },
  { ratio: '16:9', w: 1344, h: 768 },
  { ratio: '9:16', w: 768, h: 1344 }
]
interface RegenDraft {
  seed: string
  width: number
  height: number
}

const messages = ref<ChatViewMessage[]>([])
const sessions = ref<ChatSession[]>([])
const quickCommands = ref<QuickCommand[]>([])
const sessionId = ref<number>()
const input = ref('')
const sending = ref(false)
const waitingTask = ref<number | null>(null)
const flowRef = ref<HTMLElement>()
/** 任务失败状态表：task_id → 是否失败（用于气泡下方显示重试按钮） */
const taskFailed = ref<Record<number, boolean>>({})
const retryingTaskId = ref<number | null>(null)
const detailVisible = ref(false)
const detailAsset = ref<StudioAsset | null>(null)
/** 生成参数面板展开态 / 每消息重生成草稿 */
const paramOpen = ref<Record<number, boolean>>({})
const regenDraft = ref<Record<number, RegenDraft>>({})
/** 大图预览（左图右参数 + 操作） */
const preview = reactive<{ visible: boolean; asset: StudioAsset | null; snap: RegenSnapshot | null; msg: ChatViewMessage | null }>({
  visible: false,
  asset: null,
  snap: null,
  msg: null
})
/** 高级参数：随消息提交给生图链路 */
const advancedOpen = ref(false)
const advanced = reactive({ negative: '', width: 1024, height: 1024, steps: 20, cfg: 7, seed: '-1' })
const defaultModel = ref('')

interface RegenSnapshot {
  prompt: string
  negative?: string
  seed?: number
  width?: number
  height?: number
  steps?: number
  cfg?: number
}

/** 生图服务状态：全局共享 store（顶栏/工作台/本页共用同一轮询器与一键启动） */
const sysStore = useSystemStatusStore()
const { serviceDown, starting, startElapsed } = storeToRefs(sysStore)
const startService = () => sysStore.startService()

const currentTitle = computed(
  () => sessions.value.find((s) => s.id === sessionId.value)?.title || t('studio.chat.newSession')
)
const totalImgCount = computed(() => messages.value.reduce((n, m) => n + m.assetList.length, 0))

/** 任务 result → 参数快照（参数面板与预览栏数据源） */
const snapOf = (msg: ChatViewMessage): RegenSnapshot | null => {
  if (!msg.task) return null
  const result = parseMaybeJson<Record<string, any>>(msg.task.result)
  const snap = result?.params_snapshot
  if (!snap?.prompt) return null
  return {
    prompt: String(snap.prompt),
    negative: snap.negative ? String(snap.negative) : undefined,
    seed: snap.seed != null ? Number(snap.seed) : undefined,
    width: snap.width != null ? Number(snap.width) : undefined,
    height: snap.height != null ? Number(snap.height) : undefined,
    steps: snap.steps != null ? Number(snap.steps) : undefined,
    cfg: snap.cfg != null ? Number(snap.cfg) : undefined
  }
}

const ratioOf = (w?: number, h?: number): string => {
  const hit = SIZE_PRESETS.find((p) => p.w === w && p.h === h)
  return hit ? hit.ratio : ''
}

const sizeText = (snap: { width?: number; height?: number } | null) => {
  if (!snap?.width || !snap?.height) return '—'
  const r = ratioOf(snap.width, snap.height)
  return `${snap.width} × ${snap.height}${r ? ` (${r})` : ''}`
}

const draftOf = (msg: ChatViewMessage): RegenDraft => {
  if (!regenDraft.value[msg.id]) {
    const snap = snapOf(msg)
    regenDraft.value[msg.id] = {
      seed: String(snap?.seed ?? -1),
      width: snap?.width ?? 1024,
      height: snap?.height ?? 1024
    }
  }
  return regenDraft.value[msg.id]
}

const toggleParams = (id: number) => {
  paramOpen.value = { ...paramOpen.value, [id]: !paramOpen.value[id] }
}

const randomSeed = (id: number) => {
  draftOf(messages.value.find((m) => m.id === id)!)
  regenDraft.value[id] = {
    ...regenDraft.value[id],
    seed: String(Math.floor(Math.random() * 2147483647))
  }
}

const applyRatio = (id: number, p: { w: number; h: number }) => {
  regenDraft.value[id] = { ...regenDraft.value[id], width: p.w, height: p.h }
}

/** 大图预览 */
const openPreview = (asset: StudioAsset, msg: ChatViewMessage) => {
  preview.asset = asset
  preview.msg = msg
  preview.snap = snapOf(msg)
  preview.visible = true
}

/** 复制生成参数（JSON）到剪贴板 */
const copyParams = async (msg: ChatViewMessage) => {
  const snap = snapOf(msg)
  if (!snap) return
  try {
    await navigator.clipboard.writeText(JSON.stringify(snap, null, 2))
    ElMessage.success(t('studio.chat.copyOk'))
  } catch {
    ElMessage.error(t('studio.chat.copyFail'))
  }
}

/** 参考图上传占位（img2img 后端能力待接入） */
const attachHint = () => {
  ElMessage.info(t('studio.chat.attachTip'))
}

/** 清空历史 = 删除当前会话（产物保留在资产库） */
const clearHistory = async () => {
  if (sessionId.value) {
    await removeSession(sessionId.value)
  } else {
    messages.value = []
  }
}

/** 以消息参数重新生成：走会话同通道（prompt 作为用户消息落库，产物回填会话） */
const regenerateWith = (msg: ChatViewMessage) => {
  const snap = snapOf(msg)
  if (!snap) return
  const draft = regenDraft.value[msg.id]
  const params: Record<string, unknown> = {
    width: draft?.width ?? snap.width ?? 1024,
    height: draft?.height ?? snap.height ?? 1024,
    steps: snap.steps ?? 20,
    cfg: snap.cfg ?? 7,
    seed: Number(draft?.seed ?? snap.seed ?? -1) || -1
  }
  if (snap.negative) params.negative = snap.negative
  preview.visible = false
  send(snap.prompt, params)
}

/** 消息内产物详情弹窗 */
const viewAsset = async (asset: StudioAsset) => {
  detailAsset.value = asset
  detailVisible.value = true
  try {
    const res = await getAsset(asset.id)
    if (res.data) detailAsset.value = res.data
  } catch {
    // 列表数据兜底
  }
}

/** 发送消息：AI 回复带 task_id 时轮询任务，done 后刷新产物图 */
const send = async (text?: string, params?: Record<string, unknown>) => {
  const message = (text ?? input.value).trim()
  if (!message || sending.value) return
  input.value = ''
  sending.value = true

  // 本地先展示用户消息
  messages.value.push({
    id: Date.now(),
    session_id: sessionId.value ?? 0,
    role: 'user',
    content: message,
    task_id: null,
    asset_ids: '',
    created_at: new Date().toISOString(),
    assetList: []
  })
  scrollBottom()

  try {
    const res = await sendChat({ message, session_id: sessionId.value, params })
    const data = res.data
    if (data.session_id) sessionId.value = data.session_id

    const view: ChatViewMessage = { ...toView(data), assetList: [] }
    // AI 回复携带产物 id 时立即渲染
    if (data.asset_ids.length) {
      view.assetList = await fetchAssetsByIds(data.asset_ids)
    }
    messages.value.push(view)

    // 返回 task_id 则轮询任务，done 后把产物与参数快照挂到该条回复上；失败则气泡下方给出重试入口
    if (data.task_id) {
      const viewRef = view
      if (viewRef.task_id) taskFailed.value = { ...taskFailed.value, [viewRef.task_id]: false }
      waitingTask.value = data.task_id
      try {
        const task = await pollTask(data.task_id, {
          // 生图/抠图耗时取决于硬件（低配设备可能数分钟），轮询自带瞬断重试
          timeoutMs: 600000,
          onUpdate: (task) => {
            // 任务转为 failed 时立即给出明确提示（不再静默等待）
            if (task.status === 'failed') {
              ElMessage.error(t('studio.chat.taskFailedDetail', { n: task.id, msg: String(task.error || '').split('\n')[0].slice(0, 120) }))
            }
          }
        })
        viewRef.task = task
        const ids = taskAssetIds(task)
        if (ids.length) {
          view.assetList = await fetchAssetsByIds(ids)
          messages.value = [...messages.value]
        }
      } catch (error) {
        // 轮询抛错（failed/超时）：标记失败态，气泡下方显示重试按钮
        taskFailed.value = { ...taskFailed.value, [data.task_id]: true }
        ElMessage.error(error instanceof Error ? error.message : t('studio.common.taskFailedMsg'))
      } finally {
        waitingTask.value = null
      }
    }
    loadSessions()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : t('studio.chat.sendFailed'))
  } finally {
    sending.value = false
    scrollBottom()
  }
}

/** 消息气泡内失败任务的重试：调 retry API 后轮询刷新，done 后挂产物 */
const retryMsgTask = async (msg: ChatViewMessage) => {
  if (!msg.task_id || retryingTaskId.value) return
  retryingTaskId.value = msg.task_id
  taskFailed.value = { ...taskFailed.value, [msg.task_id]: false }
  try {
    await retryTask(msg.task_id)
    ElMessage.success(t('studio.chat.taskRequeued', { n: msg.task_id }))
    const task = await pollTask(msg.task_id)
    msg.task = task
    const ids = taskAssetIds(task)
    if (ids.length) {
      msg.assetList = await fetchAssetsByIds(ids)
      messages.value = [...messages.value]
    }
  } catch (error) {
    // 重试后仍失败：恢复失败标记，保留重试按钮
    if (msg.task_id) taskFailed.value = { ...taskFailed.value, [msg.task_id]: true }
    ElMessage.error(error instanceof Error ? error.message : t('studio.chat.retryFailed'))
  } finally {
    retryingTaskId.value = null
    scrollBottom()
  }
}

/** 后端返回 → 视图消息 */
const toView = (data: { message_id: number; content: string; created_at?: string }): ChatMessage => ({
  id: data.message_id,
  session_id: sessionId.value ?? 0,
  role: 'assistant',
  content: data.content,
  task_id: null,
  asset_ids: '',
  created_at: data.created_at ?? new Date().toISOString()
})

/** 切换会话并加载历史消息 */
const switchSession = async (id: number) => {
  sessionId.value = id
  try {
    const res = await listChatMessages(id)
    const list: ChatViewMessage[] = []
    const failedMap: Record<number, boolean> = {}
    for (const msg of res.data ?? []) {
      let ids = msg.asset_ids
        ? msg.asset_ids
            .split(',')
            .map((v) => Number(v))
            .filter((v) => Number.isFinite(v) && v > 0)
        : []
      // 关联任务：参数面板数据源 + failed 重试入口 + 存量消息的产物兜底
      let taskData: StudioTask | undefined
      if (msg.task_id) {
        try {
          const task = await getTask(msg.task_id)
          taskData = task.data ?? undefined
          if (!ids.length) ids = taskAssetIds(taskData ?? ({} as StudioTask))
          if (taskData?.status === 'failed') failedMap[msg.task_id] = true
        } catch {
          // 任务查询失败时忽略，不影响消息渲染
        }
      }
      list.push({ ...msg, task: taskData, assetList: await fetchAssetsByIds(ids) })
    }
    messages.value = list
    taskFailed.value = failedMap
    scrollBottom()
  } catch {
    ElMessage.error(t('studio.chat.loadMessagesFailed'))
  }
}

const newSession = () => {
  sessionId.value = undefined
  messages.value = []
}

const loadSessions = async () => {
  try {
    const res = await listChatSessions()
    sessions.value = res.data ?? []
  } catch {
    // 静默：侧栏会话列表加载失败不阻塞主流程
  }
}

/** 删除会话：移除会话与消息记录；图片资产保留在资产库（到资产库中删除） */
const removeSession = async (id: number) => {
  try {
    await ElMessageBox.confirm(t('studio.chat.confirmDelete', { n: id }), t('studio.chat.deleteSession'), {
      type: 'warning',
      confirmButtonText: t('studio.common.actions.confirm'),
      cancelButtonText: t('studio.common.actions.cancel')
    })
  } catch {
    return
  }
  try {
    await deleteChatSession(id)
    ElMessage.success(t('studio.chat.sessionDeleted'))
    await loadSessions()
    // 删除的是当前会话：清空视图并切入最近一个会话
    if (sessionId.value === id) {
      sessionId.value = undefined
      messages.value = []
      waitingTask.value = null
      if (sessions.value.length) await switchSession(sessions.value[0].id)
    }
  } catch {
    // 请求层已统一弹错误提示
  }
}

const formatTime = (iso: string) => {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

/** 会话列表时间：MM-DD HH:mm */
const formatSessionTime = (iso: string) => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const pad = (v: number) => String(v).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const scrollBottom = () => {
  nextTick(() => flowRef.value?.scrollTo({ top: flowRef.value.scrollHeight, behavior: 'smooth' }))
}

onMounted(async () => {
  await loadSessions()
  // 默认进入最近一个会话，无会话则等待首条消息创建
  if (sessions.value.length) await switchSession(sessions.value[0].id)
  try {
    const res = await getQuickCommands()
    quickCommands.value = res.data ?? []
  } catch {
    // 快捷指令拉取失败时使用空列表
  }
  // 生图服务状态刷新：未启动时页面顶部横幅给出一键启动入口（轮询由顶栏共享 store 负责）
  await sysStore.fetchStatus()
  // 底部模型标识：默认底模名
  try {
    const res = await listModels('checkpoint')
    const def = (res.data ?? []).find((m) => m.is_default) ?? (res.data ?? [])[0]
    if (def) defaultModel.value = def.name
  } catch {
    // 模型列表失败不影响页面
  }
})
</script>

<style lang="scss" scoped>
  .chat-page {
    .chat-layout {
      display: flex;
      gap: 14px;
      height: calc(100vh - 200px);
      min-height: 480px;
    }

    /* ---- 左侧会话栏 ---- */
    .chat-side {
      display: flex;
      flex-direction: column;
      width: 252px;
      flex-shrink: 0;
      overflow: hidden;

      .new-session-btn {
        width: 100%;
        margin-bottom: 10px;
      }

      .session-list {
        flex: 1;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 2px;
      }

      .session-item {
        display: flex;
        align-items: center;
        gap: 9px;
        padding: 8px;
        border-radius: 8px;
        cursor: pointer;
        border: 1px solid transparent;
        transition: all 0.15s;

        .session-thumb {
          width: 44px;
          height: 44px;
          flex-shrink: 0;
          border-radius: 8px;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--art-gray-200);
          font-size: 18px;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }

        .session-meta {
          flex: 1;
          min-width: 0;
          display: flex;
          flex-direction: column;
          gap: 3px;

          .session-title {
            font-size: 12.5px;
            font-weight: 500;
            color: var(--art-text-gray-900);
          }

          .session-time {
            font-size: 10.5px;
            color: var(--art-gray-500);
          }
        }

        .session-del {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 18px;
          height: 18px;
          flex-shrink: 0;
          font-size: 14px;
          line-height: 1;
          color: var(--art-gray-400, #98a2b3);
          border-radius: 4px;
          opacity: 0;
          transition: all 0.15s;

          &:hover {
            color: #f87171;
            background: rgba(248, 113, 113, 0.12);
          }
        }

        &:hover {
          background: var(--art-gray-200);

          .session-del {
            opacity: 1;
          }
        }

        &.on {
          background: rgba(37, 99, 235, 0.12);
          border-color: rgba(37, 99, 235, 0.4);

          .session-title {
            color: var(--art-primary);
            font-weight: 600;
          }

          .session-del {
            opacity: 0.6;
          }

          &:hover .session-del {
            opacity: 1;
          }
        }
      }
    }

    /* ---- 主区 ---- */
    .chat-main {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      background: var(--art-main-bg-color);
      border: 1px solid var(--art-border-dashed-color);
      border-radius: 8px;
      overflow: hidden;

      .chat-head {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        border-bottom: 1px solid var(--art-border-dashed-color);

        .chat-head-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--art-text-gray-900);
        }

        .chat-head-stats {
          font-size: 11.5px;
          color: var(--art-gray-500);
        }
      }

      .chat-flow {
        flex: 1;
        overflow-y: auto;
        padding: 18px 20px;
      }
    }

    .chat-msg {
      display: flex;
      gap: 10px;
      margin-bottom: 18px;

      &.rev {
        flex-direction: row-reverse;

        .chat-bubble {
          background: rgba(37, 99, 235, 0.1);
        }

        .msg-text {
          text-align: right;
        }
      }

      .chat-ava {
        width: 34px;
        height: 34px;
        flex-shrink: 0;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 600;
        color: #fff;
        background: #64748b;

        &.ai {
          background: linear-gradient(135deg, #2563eb, #06b6d4);
        }
      }

      .chat-bubble {
        max-width: min(620px, 78%);
        background: var(--art-gray-100);
        border-radius: 10px;
        padding: 10px 14px;

        .msg-text {
          font-size: 13px;
          line-height: 1.65;
          color: var(--art-text-gray-900);
          white-space: pre-wrap;
          word-break: break-word;
        }

        .time {
          display: block;
          margin-top: 6px;
          font-size: 10.5px;
          color: var(--art-gray-500);
        }
      }

      .msg-imgs {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 10px;
      }

      .chat-img {
        max-width: 380px;

        > img {
          width: 100%;
          display: block;
          border-radius: 8px;
          cursor: zoom-in;
        }
      }
    }

    /* 消息内嵌生成参数面板 */
    .gen-params {
      margin-top: 8px;
      border: 1px solid var(--art-border-dashed-color);
      border-radius: 8px;
      overflow: hidden;
      background: var(--art-main-bg-color);

      .gp-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 7px 10px;
        font-size: 12px;
        font-weight: 600;
        color: var(--art-gray-600);
        cursor: pointer;
        user-select: none;

        &:hover {
          background: var(--art-gray-100);
        }

        .gp-arrow {
          transition: transform 0.2s;

          &.open {
            transform: rotate(180deg);
          }
        }
      }

      .gp-body {
        padding: 10px 12px;
        border-top: 1px solid var(--art-border-dashed-color);
      }

      .gp-row {
        display: flex;
        gap: 10px;
        margin-bottom: 6px;
        font-size: 12px;
        line-height: 1.55;

        .k {
          width: 62px;
          flex-shrink: 0;
          color: var(--art-gray-500);
        }

        .v {
          color: var(--art-text-gray-900);
          word-break: break-word;
        }
      }

      .gp-regen {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px dashed var(--art-border-dashed-color);

        .gp-regen-tip {
          font-size: 11px;
          color: var(--art-gray-500);
          margin-bottom: 8px;
        }

        .gp-regen-seed {
          display: flex;
          gap: 8px;
          margin-bottom: 8px;
        }

        .gp-regen-btn {
          width: 100%;
          margin-top: 8px;
        }
      }

      .gp-ops {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-top: 10px;
        font-size: 12px;
        color: var(--art-gray-600);

        span,
        a {
          cursor: pointer;
          color: var(--art-gray-600);

          &:hover {
            color: var(--art-primary);
          }
        }

        a {
          text-decoration: none;
        }
      }
    }

    /* 比例快捷 chips */
    .ratio-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;

      .ratio-chip {
        padding: 3px 10px;
        font-size: 11.5px;
        border: 1px solid var(--art-border-dashed-color);
        border-radius: 5px;
        cursor: pointer;
        color: var(--art-gray-600);
        transition: all 0.15s;

        &:hover {
          border-color: var(--art-primary);
        }

        &.on {
          background: rgba(37, 99, 235, 0.12);
          border-color: var(--art-primary);
          color: var(--art-primary);
          font-weight: 600;
        }
      }
    }

    .task-retry-row {
      margin-top: 8px;
    }

    /* 高级参数条与面板 */
    .advanced-bar {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 7px 16px;
      border-top: 1px solid var(--art-border-dashed-color);
      font-size: 11.5px;
      color: var(--art-gray-500);

      .adv-toggle {
        cursor: pointer;
        user-select: none;

        &:hover {
          color: var(--art-primary);
        }

        i {
          display: inline-block;
          transition: transform 0.2s;

          &.open {
            transform: rotate(180deg);
          }
        }
      }

      .adv-model {
        flex: 1;
      }

      .adv-clear {
        cursor: pointer;

        &:hover {
          color: #f87171;
        }
      }
    }

    .advanced-panel {
      padding: 10px 16px;
      border-top: 1px dashed var(--art-border-dashed-color);
      display: flex;
      flex-direction: column;
      gap: 10px;

      .adv-row {
        display: flex;
        align-items: flex-start;
        gap: 10px;

        &.three {
          align-items: center;

          .k {
            flex-shrink: 0;
          }
        }

        .k {
          width: 62px;
          flex-shrink: 0;
          font-size: 12px;
          color: var(--art-gray-500);
          line-height: 2;
        }

        .el-textarea,
        .ratio-chips {
          flex: 1;
        }
      }
    }

    /* 底部输入区 */
    .chat-input {
      padding: 10px 16px 14px;
      border-top: 1px solid var(--art-border-dashed-color);

      .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 8px;

        .quick-chip {
          padding: 3px 10px;
          font-size: 11px;
          color: var(--art-gray-600);
          background: var(--art-gray-100);
          border-radius: 999px;
          cursor: pointer;

          &:hover {
            color: var(--art-primary);
            background: rgba(37, 99, 235, 0.08);
          }
        }
      }

      .input-row {
        display: flex;
        align-items: flex-end;
        gap: 10px;

        .attach-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 34px;
          height: 34px;
          font-size: 16px;
          border-radius: 6px;
          cursor: pointer;
          color: var(--art-gray-600);

          &:hover {
            background: var(--art-gray-100);
          }
        }

        .el-textarea {
          flex: 1;
        }

        .send-btn {
          width: 40px;
          height: 40px;
          font-size: 16px;
          padding: 0;
        }
      }
    }
  }

  /* 大图预览弹窗（teleport 到 body，内容节点仍带本组件 scope 属性） */
  .preview-wrap {
    display: flex;
    gap: 0;
    background: #0b1020;
    border-radius: 10px;
    overflow: hidden;

    .preview-img {
      flex: 1;
      min-width: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #05070f;

      img {
        max-width: 100%;
        max-height: 78vh;
        object-fit: contain;
        display: block;
      }
    }

    .preview-side {
      width: 320px;
      flex-shrink: 0;
      padding: 20px 18px;
      overflow-y: auto;
      max-height: 78vh;
      color: var(--art-text-gray-900);

      .pv-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 14px;

        .size-tag {
          padding: 1px 8px;
          font-size: 11px;
          font-weight: 500;
          color: #22d3ee;
          background: rgba(34, 211, 238, 0.1);
          border: 1px solid rgba(34, 211, 238, 0.35);
          border-radius: 999px;
        }
      }

      .pv-k {
        font-size: 11px;
        color: var(--art-gray-500);
        margin: 10px 0 4px;
      }

      .pv-v {
        font-size: 12.5px;
        line-height: 1.6;
        word-break: break-word;
      }

      .pv-ops {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 18px;

        .pv-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 9px 0;
          font-size: 12.5px;
          border: 1px solid var(--art-border-dashed-color);
          border-radius: 8px;
          cursor: pointer;
          color: var(--art-text-gray-900);
          text-decoration: none;
          transition: all 0.15s;

          &:hover {
            border-color: var(--art-primary);
            color: var(--art-primary);
          }

          &.disabled {
            opacity: 0.55;
            cursor: not-allowed;

            &:hover {
              border-color: var(--art-border-dashed-color);
              color: var(--art-text-gray-900);
            }
          }
        }
      }
    }
  }
</style>

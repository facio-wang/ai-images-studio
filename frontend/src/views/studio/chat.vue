<!-- 对话工作台：聊天流 + 消息内嵌产物 + 快捷指令 + 右侧会话资产面板 -->
<template>
  <div class="studio-page chat-page">
    <div class="page-head">
      <div>
        <h1>对话工作台</h1>
        <p class="desc">一句话完成生图 / 抠图 / 查询，产物自动入资产库</p>
      </div>
      <ElButton @click="newSession">＋ 新建会话</ElButton>
    </div>

    <div class="chat-tip studio-card">
      💡 对话模式 · 所有图片处理都可以在这里用一句话完成
      <span class="tip-right">生图 · 抠图 · 资产/任务查询</span>
    </div>

    <!-- 生图服务未启动横幅（移植自 webUI-v1.0 健康指示灯） -->
    <ElAlert
      v-if="serviceDown"
      type="warning"
      :closable="false"
      show-icon
      title="生图服务（ComfyUI 8188）未启动：发送生图/抠图请求会直接得到失败提示"
      description="请在 Win11 宿主机启动 ComfyUI 后刷新本页；查询类对话不受影响。"
      style="margin-bottom: 14px"
    />

    <div class="chat-layout">
      <!-- 中间聊天流 -->
      <div class="chat-main studio-card">
        <div ref="flowRef" class="chat-flow">
          <div v-for="msg in messages" :key="msg.id" class="chat-msg" :class="{ rev: msg.role === 'user' }">
            <!-- 头像：圆形字母 -->
            <div class="chat-ava" :class="msg.role">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
            <div class="chat-bubble">
              <div class="msg-text">{{ msg.content }}</div>
              <!-- 消息内嵌产物图 -->
              <div v-if="msg.assetList.length" class="msg-imgs">
                <div
                  v-for="asset in msg.assetList"
                  :key="asset.id"
                  class="chat-img"
                  :class="{ checker: asset.type === 'matting' }"
                >
                  <img :src="asset.url" :alt="asset.labels || asset.filename || `资产#${asset.id}`" />
                  <div class="thumb-ops">
                    <ElButton size="small" @click="viewAsset(asset)">🔍 详情</ElButton>
                    <ElButton size="small" tag="a" :href="asset.url" target="_blank">⬇ 下载</ElButton>
                  </div>
                </div>
              </div>
              <span class="time">{{ formatTime(msg.created_at) }}</span>
              <!-- 关联任务失败：气泡下方提供「重试任务」入口 -->
              <div v-if="msg.task_id && taskFailed[msg.task_id]" class="task-retry-row">
                <ElButton size="small" type="warning" plain :loading="retryingTaskId === msg.task_id" @click="retryMsgTask(msg)">
                  ⟳ 重试任务 #{{ msg.task_id }}
                </ElButton>
              </div>
            </div>
          </div>

          <div v-if="waitingTask" class="chat-msg">
            <div class="chat-ava ai">AI</div>
            <div class="chat-bubble">
              <div class="msg-text">任务 #{{ waitingTask }} 执行中，完成后自动展示产物…</div>
              <ElIcon class="is-loading spin"><Loading /></ElIcon>
            </div>
          </div>

          <div v-if="!messages.length && !waitingTask" class="studio-empty">
            <span>开始与 AI 对话，例如「生成一张赛博朋克城市夜景」</span>
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
            <ElInput
              v-model="input"
              type="textarea"
              :rows="2"
              resize="none"
              placeholder="描述你想做的图片处理，例如：生成一张赛博朋克风格的城市夜景…"
              @keydown.enter.exact.prevent="send()"
            />
            <ElButton type="primary" :loading="sending" @click="send()">发送 ➤</ElButton>
          </div>
        </div>
      </div>

      <!-- 右侧会话资产面板 -->
      <div class="chat-side">
        <div class="studio-card">
          <div class="card-title">历史会话</div>
          <div class="session-list">
            <div
              v-for="s in sessions"
              :key="s.id"
              class="session-item"
              :class="{ on: s.id === sessionId }"
              @click="switchSession(s.id)"
            >
              <span class="truncate">会话 #{{ s.id }} · {{ s.title }}</span>
            </div>
            <div v-if="!sessions.length" class="studio-empty"><span>暂无历史会话</span></div>
          </div>
        </div>

        <div class="studio-card">
          <div class="card-title">会话产物</div>
          <div class="side-assets">
            <div v-for="asset in sessionAssets" :key="asset.id" class="side-asset">
              <div class="studio-thumb side-thumb" :class="{ checker: asset.type === 'matting' }">
                <img :src="asset.thumb_url" loading="lazy" />
              </div>
              <div class="side-asset-meta">
                <span class="truncate">#{{ asset.id }} {{ asset.labels || asset.filename || '未命名' }}</span>
                <span class="badge-row"><i :class="ASSET_BADGE_CLASS[asset.type]">{{ TASK_TYPE_TEXT[asset.type] }}</i></span>
              </div>
            </div>
            <div v-if="!sessionAssets.length" class="studio-empty"><span>本会话暂无产物</span></div>
          </div>
        </div>
      </div>
    </div>
    <!-- 生成详情弹窗：完整提示词 / 模型 / 参数 -->
    <GenDetailDialog v-model="detailVisible" :asset="detailAsset" />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  ChatMessage,
  ChatSession,
  QuickCommand,
  StudioAsset,
  fetchAssetsByIds,
  getAsset,
  getQuickCommands,
  getSystemStatus,
  getTask,
  listChatMessages,
  listChatSessions,
  pollTask,
  retryTask,
  sendChat,
  SystemStatus,
  taskAssetIds
} from '@/api/studio'
import { ASSET_BADGE_CLASS, TASK_TYPE_TEXT } from './utils'
import GenDetailDialog from './components/GenDetailDialog.vue'
import './style.scss'

defineOptions({ name: 'StudioChat' })

interface ChatViewMessage extends ChatMessage {
  assetList: StudioAsset[]
}

const messages = ref<ChatViewMessage[]>([])
const sessions = ref<ChatSession[]>([])
const sessionAssets = ref<StudioAsset[]>([])
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
const serviceDown = ref(false)

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
const send = async (text?: string) => {
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
    const res = await sendChat({ message, session_id: sessionId.value })
    const data = res.data
    if (data.session_id) sessionId.value = data.session_id

    const view: ChatViewMessage = { ...toView(data), assetList: [] }
    // AI 回复携带产物 id 时立即渲染
    if (data.asset_ids.length) {
      view.assetList = await fetchAssetsByIds(data.asset_ids)
    }
    messages.value.push(view)

    // 返回 task_id 则轮询任务，done 后把产物挂到该条回复上；失败则气泡下方给出重试入口
    if (data.task_id) {
      const viewRef = view
      if (viewRef.task_id) taskFailed.value = { ...taskFailed.value, [viewRef.task_id]: false }
      waitingTask.value = data.task_id
      try {
        const task = await pollTask(data.task_id, {
          // 生图/抠图耗时取决于硬件（低配设备可能数分钟），轮询自带瞬断重试
          timeoutMs: 600000,
          onUpdate: (t) => {
            // 任务转为 failed 时立即给出明确提示（不再静默等待）
            if (t.status === 'failed') {
              ElMessage.error(`任务 #${t.id} 失败：${String(t.error || '').split('\n')[0].slice(0, 120)}`)
            }
          }
        })
        const ids = taskAssetIds(task)
        if (ids.length) {
          view.assetList = await fetchAssetsByIds(ids)
          messages.value = [...messages.value]
        }
        refreshSessionAssets()
      } catch (error) {
        // 轮询抛错（failed/超时）：标记失败态，气泡下方显示重试按钮
        taskFailed.value = { ...taskFailed.value, [data.task_id]: true }
        ElMessage.error(error instanceof Error ? error.message : '任务执行失败')
      } finally {
        waitingTask.value = null
      }
    }
    loadSessions()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '发送失败')
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
    ElMessage.success(`任务 #${msg.task_id} 已重新入队`)
    const task = await pollTask(msg.task_id)
    const ids = taskAssetIds(task)
    if (ids.length) {
      msg.assetList = await fetchAssetsByIds(ids)
      messages.value = [...messages.value]
    }
    refreshSessionAssets()
  } catch (error) {
    // 重试后仍失败：恢复失败标记，保留重试按钮
    if (msg.task_id) taskFailed.value = { ...taskFailed.value, [msg.task_id]: true }
    ElMessage.error(error instanceof Error ? error.message : '重试失败')
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
      const ids = msg.asset_ids
        ? msg.asset_ids
            .split(',')
            .map((v) => Number(v))
            .filter((v) => Number.isFinite(v) && v > 0)
        : []
      list.push({ ...msg, assetList: await fetchAssetsByIds(ids) })
      // 历史消息中关联任务为 failed 时，也提供重试入口
      if (msg.task_id) {
        try {
          const t = await getTask(msg.task_id)
          if (t.data?.status === 'failed') failedMap[msg.task_id] = true
        } catch {
          // 任务查询失败时忽略，不影响消息渲染
        }
      }
    }
    messages.value = list
    taskFailed.value = failedMap
    refreshSessionAssets()
    scrollBottom()
  } catch {
    ElMessage.error('加载会话消息失败')
  }
}

const newSession = () => {
  sessionId.value = undefined
  messages.value = []
  sessionAssets.value = []
}

const loadSessions = async () => {
  try {
    const res = await listChatSessions()
    sessions.value = res.data ?? []
  } catch {
    // 静默：侧栏会话列表加载失败不阻塞主流程
  }
}

/** 汇总当前会话消息中的产物到右侧面板 */
const refreshSessionAssets = () => {
  const map = new Map<number, StudioAsset>()
  messages.value.forEach((m) => m.assetList.forEach((a) => map.set(a.id, a)))
  sessionAssets.value = [...map.values()]
}

const formatTime = (iso: string) => {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
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
  // 生图服务状态预检：未启动时页面顶部给横幅提示（移植自 webUI-v1.0 健康指示灯）
  try {
    const res = await getSystemStatus()
    serviceDown.value = res.data?.comfyui.status !== 'running'
  } catch {
    serviceDown.value = false
  }
})
</script>

<style lang="scss" scoped>
  .chat-page {
    .page-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;

      h1 {
        font-size: 20px;
        font-weight: 700;
        color: var(--art-text-gray-900);
      }

      .desc {
        font-size: 12px;
        color: var(--art-gray-600);
        margin-top: 2px;
      }
    }

    .chat-tip {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      margin-bottom: 14px;
      font-size: 12px;
      color: var(--art-primary);
      background: rgba(37, 99, 235, 0.1);
      border-color: rgba(37, 99, 235, 0.35);

      .tip-right {
        margin-left: auto;
        color: var(--art-gray-500);
        font-size: 11px;
      }
    }

    .chat-layout {
      display: grid;
      grid-template-columns: minmax(0, 8fr) minmax(240px, 4fr);
      gap: 16px;
      align-items: start;
    }

    .chat-main {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 260px);
      min-height: 480px;
      padding: 0;
    }

    .chat-flow {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
    }

    .chat-msg {
      display: flex;
      gap: 10px;
      margin-bottom: 18px;

      &.rev {
        flex-direction: row-reverse;

        .chat-bubble {
          background: rgba(37, 99, 235, 0.14);
          border-color: rgba(37, 99, 235, 0.35);
        }
      }
    }

    .chat-ava {
      width: 32px;
      height: 32px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      font-size: 12px;
      font-weight: 700;
      color: #fff;

      &.ai {
        background: linear-gradient(135deg, #2563eb, #06b6d4);
      }

      &.user {
        background: linear-gradient(135deg, #7c3aed, #2563eb);
      }
    }

    .chat-bubble {
      max-width: 78%;
      padding: 10px 14px;
      border-radius: 8px;
      background: var(--art-main-bg-color);
      border: 1px solid var(--art-border-dashed-color);
      font-size: 13px;
      line-height: 1.65;
      white-space: pre-wrap;
      word-break: break-word;

      .msg-imgs {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
      }

      .chat-img {
        position: relative;
        width: 144px;
        height: 144px;
        border-radius: 6px;
        overflow: hidden;
        background: var(--art-gray-200);

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .time {
        display: block;
        font-size: 10px;
        color: var(--art-gray-500);
        margin-top: 4px;
      }

      .task-retry-row {
        margin-top: 8px;
      }
    }

    .spin {
      margin-top: 6px;
      color: var(--art-primary);
    }

    .chat-input {
      border-top: 1px solid var(--art-border-dashed-color);
      padding: 12px 14px;
      background: var(--art-gray-100);

      .chips {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 10px;
      }

      .input-row {
        display: flex;
        align-items: flex-end;
        gap: 8px;
      }
    }

    .chat-side {
      display: flex;
      flex-direction: column;
      gap: 16px;
      max-height: calc(100vh - 260px);
      overflow-y: auto;
    }

    .session-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-height: 200px;
      overflow-y: auto;
    }

    .session-item {
      padding: 8px 10px;
      border-radius: 6px;
      font-size: 12px;
      color: var(--art-gray-600);
      cursor: pointer;
      border: 1px solid transparent;

      &:hover {
        background: var(--art-gray-200);
      }

      &.on {
        background: rgba(37, 99, 235, 0.12);
        border-color: rgba(37, 99, 235, 0.4);
        color: var(--art-primary);
        font-weight: 600;
      }
    }

    .side-assets {
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: 420px;
      overflow-y: auto;
    }

    .side-asset {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .side-thumb {
      width: 44px;
      height: 44px;
      flex-shrink: 0;
      border-radius: 6px;
    }

    .side-asset-meta {
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-size: 12px;

      .badge-row .asset-badge {
        font-size: 10px;
      }
    }

    .truncate {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
</style>

/**
 * AI Images Studio 后端 API 统一封装
 *
 * - 统一响应 {code, msg, data}，401 时由 http 拦截器统一跳回登录页
 * - Token 由登录页写入 user store（pinia persist 到 localStorage），
 *   http 请求拦截器自动附加 Authorization: Bearer <token>
 */
import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

// ---------- 类型定义 ----------

/** 模型类别：底模 / LoRA / 翻译 / 抠图 */
export type ModelCategory = 'checkpoint' | 'lora' | 'translate' | 'matting'

export interface StudioModel {
  id: number
  category: ModelCategory
  name: string
  enabled: number | boolean
  is_default: number | boolean
  meta: string
  created_at: string
}

export type TaskType = 'generate' | 'matting'
export type TaskStatus = 'queued' | 'running' | 'done' | 'failed'

export interface StudioTask {
  id: number
  type: TaskType
  status: TaskStatus
  params: Record<string, any> | string
  result: Record<string, any> | string
  error: string | null
  retry_count: number
  created_at: string
  updated_at?: string
}

export interface StudioAsset {
  id: number
  type: 'generate' | 'matting' | 'upload'
  file_path: string
  thumb_path: string | null
  filename?: string | null
  labels?: string | null
  source_task_id?: number | null
  created_at: string
  /** 详情弹窗用：源任务完整信息（params/result/error） */
  task?: StudioTask | null
  /** 后端拼接好的静态访问地址（/files/xxx.png） */
  url: string
  thumb_url: string
}

export interface ChatSendResult {
  session_id: number
  message_id: number
  content: string
  intent: string
  task_id: number | null
  asset_ids: number[]
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  task_id: number | null
  /** 逗号分隔的资产 id */
  asset_ids: string
  created_at: string
}

export interface ChatSession {
  id: number
  title: string
  created_at: string
}

export interface QuickCommand {
  label: string
  text: string
}

/** 解析后端可能返回 JSON 字符串/对象的字段 */
function parseMaybeJson<T>(value: unknown): T {
  if (typeof value === 'string') {
    try {
      return JSON.parse(value) as T
    } catch {
      return {} as T
    }
  }
  return (value ?? {}) as T
}

// ---------- 鉴权 / 元信息 ----------

export interface SystemMeta {
  name: string
  version: string
}

/** 校验 token 是否有效（登录页用）：后端 / 无需鉴权，携带待验证的 Authorization 头调受保护接口 */
export async function verifyToken(token: string): Promise<boolean> {
  try {
    await request.get<BaseResponse<StudioModel[]>>({
      url: '/api/models',
      headers: { Authorization: `Bearer ${token}` },
      requestOptions: { errorMessageMode: 'none' }
    })
    return true
  } catch {
    return false
  }
}

// ---------- 模型中心 ----------

/** 模型列表（category 可选过滤） */
export function listModels(category?: ModelCategory) {
  return request.get<BaseResponse<StudioModel[]>>({
    url: '/api/models',
    params: category ? { category } : undefined
  })
}

/** 新增模型 */
export function addModel(data: { category: ModelCategory; name: string; meta?: Record<string, any> }) {
  return request.post<BaseResponse<StudioModel>>({ url: '/api/models', data })
}

/** 更新模型（启停 / 设默认 / meta），后端为 PATCH */
export function updateModel(id: number, data: { name?: string; enabled?: boolean; is_default?: boolean; meta?: Record<string, any> }) {
  return request.request<BaseResponse<StudioModel>>({ url: `/api/models/${id}`, data, method: 'PATCH' })
}

/** 删除模型 */
export function deleteModel(id: number) {
  return request.del<BaseResponse<{ deleted: boolean }>>({ url: `/api/models/${id}` })
}

/** 从 ComfyUI 同步底模列表 */
export function syncCheckpointsApi() {
  return request.post<BaseResponse<{ added: number; total: number }>>({
    url: '/api/models/sync-checkpoints',
    timeout: 30000
  })
}

// ---------- 系统信息 ----------

export interface SystemMeta {
  name: string
  version: string
}

/**
 * 系统元信息：docker 模式下根路径 / 让位给前端 SPA，后端把 JSON 元信息挪到 /api/meta；
 * 开发模式直连 8191 时元信息仍在根路径，故先试 /api/meta 失败后回落 /
 */
export async function getSystemMeta() {
  try {
    return await request.get<BaseResponse<SystemMeta>>({ url: '/api/meta' })
  } catch {
    return request.get<BaseResponse<SystemMeta>>({ url: '/' })
  }
}

// ---------- 系统状态（移植自 webUI-v1.0：服务状态 + 硬件资源） ----------

export interface ComfyDevice {
  name: string | null
  type: string | null
  vram_total_mb: number | null
  vram_free_mb: number | null
  torch_version: string | null
}

export interface SystemStatus {
  studio: { name: string; version: string; uptime_seconds: number }
  comfyui: {
    url: string
    status: 'running' | 'stopped'
    version: string | null
    devices: ComfyDevice[]
    ram_total_mb: number | null
    ram_free_mb: number | null
    queue_running: number
    queue_pending: number
  }
}

/** 系统状态：ComfyUI 连通性 + GPU 显存/系统内存 + 队列 */
export function getSystemStatus() {
  return request.get<BaseResponse<SystemStatus>>({ url: '/api/system/status', timeout: 10000 })
}

// ---------- 生图 ----------

export interface GenerateParams {
  prompt: string
  checkpoint?: string
  width?: number
  height?: number
  steps?: number
  cfg?: number
  seed?: number
  count?: number
  /** 海报文字叠加配置（可选，透传给后端渲染） */
  texts?: PosterTextItem[]
}

/** 海报文字叠加：单个文字元素配置 */
export interface PosterTextItem {
  content: string
  /** 像素或百分比字符串（如 "50%"） */
  x: number | string
  y: number | string
  size?: number
  color?: string
  align?: 'left' | 'center' | 'right'
  bold?: boolean
  stroke_color?: string
  stroke_width?: number
  /** 半透明底衬条颜色（如 "#000000CC"） */
  bg?: string | null
}

/** 海报文字预览：上传图片 + 文字配置 → PNG Blob（request 封装已解包 res.data） */
export function previewPosterTexts(image: Blob | File, texts: PosterTextItem[]): Promise<Blob> {
  const form = new FormData()
  form.append('image', image, 'preview.png')
  form.append('texts', JSON.stringify(texts))
  return request.post<Blob>({
    url: '/api/poster/preview',
    data: form,
    responseType: 'blob',
    timeout: 30000
  })
}

/** 提交生图任务 */
export function submitGenerate(params: GenerateParams) {
  return request.post<BaseResponse<StudioTask>>({ url: '/api/generate', data: params, timeout: 30000 })
}

// ---------- 抠图 ----------

/** 用已有资产提交抠图任务 */
export function submitMatting(data: { asset_id: number; model?: string; label?: string }) {
  return request.post<BaseResponse<StudioTask>>({ url: '/api/matting', data, timeout: 30000 })
}

/** 直接上传图片并提交抠图任务（body 为原始图片字节） */
export function uploadMatting(file: File, model: string) {
  return request.post<BaseResponse<StudioTask>>({
    url: `/api/matting/upload?model=${encodeURIComponent(model)}`,
    data: file,
    timeout: 60000
  })
}

// ---------- 资产库 ----------

export interface AssetListResult {
  total: number
  items: StudioAsset[]
  page: number
  page_size: number
}

/** 资产列表（分页 + 类型筛选） */
export function listAssets(params?: { type?: string; keyword?: string; page?: number; page_size?: number }) {
  return request.get<BaseResponse<AssetListResult>>({ url: '/api/assets', params })
}

/** 资产详情 */
export function getAsset(id: number) {
  return request.get<BaseResponse<StudioAsset>>({ url: `/api/assets/${id}` })
}

/** 删除资产（同时删除磁盘文件） */
export function deleteAsset(id: number) {
  return request.del<BaseResponse<{ deleted: boolean }>>({ url: `/api/assets/${id}` })
}

/** 上传图片入库（type=upload） */
export function uploadAsset(file: File, label = '') {
  return request.post<BaseResponse<StudioAsset>>({
    url: `/api/assets/upload?label=${encodeURIComponent(label)}`,
    data: file,
    timeout: 60000
  })
}

/** 按 id 批量拉取资产详情（对话消息内嵌产物图用） */
export async function fetchAssetsByIds(ids: number[]): Promise<StudioAsset[]> {
  if (!ids.length) return []
  // 并发拉取，单个失败（如已删除）静默跳过
  const results = await Promise.all(
    ids.map((id) =>
      getAsset(id)
        .then((res) => res.data)
        .catch(() => null)
    )
  )
  return results.filter((item): item is StudioAsset => item !== null)
}

// ---------- 任务中心 ----------

/** 任务列表 */
export function listTasks(params?: { status?: string; limit?: number }) {
  return request.get<BaseResponse<StudioTask[]>>({ url: '/api/tasks', params })
}

/** 任务详情 */
export function getTask(id: number) {
  return request.get<BaseResponse<StudioTask>>({ url: `/api/tasks/${id}` })
}

/** 重试失败任务 */
export function retryTask(id: number) {
  return request.post<BaseResponse<StudioTask>>({ url: `/api/tasks/${id}/retry` })
}

/**
 * 轮询任务直至 done / failed
 *
 * 容错设计（低配设备/并发推理场景）：
 * - 单次状态查询失败（网络抖动/服务繁忙）按退避重试，连续 10 次失败才判定失联，
 *   避免后端 CPU 饱和时偶发超时就把整个等待打断（历史 bug：抠图推理期间轮询报 X_X）
 * - 超时上限按任务类型传入（生图/抠图在低配设备上可能远超默认值）
 * @throws 超时、连续失联或任务失败时抛出错误（message 为任务 error）
 */
export async function pollTask(
  taskId: number,
  options?: {
    intervalMs?: number
    timeoutMs?: number
    onUpdate?: (task: StudioTask, elapsedSec: number) => void
  }
): Promise<StudioTask> {
  const interval = options?.intervalMs ?? 1500
  const timeout = options?.timeoutMs ?? 300000
  const start = Date.now()
  let fails = 0
  for (;;) {
    let task: StudioTask
    try {
      const res = await getTask(taskId)
      task = res.data
      fails = 0
    } catch {
      fails++
      const elapsedSec = Math.round((Date.now() - start) / 1000)
      if (fails >= 10) throw new Error('无法连接后端服务，请确认服务运行中（已等待 ' + elapsedSec + 's）')
      if (Date.now() - start > timeout) throw new Error('任务超时，请稍后在任务中心查看')
      await new Promise((resolve) => setTimeout(resolve, Math.min(interval * fails, 8000)))
      continue
    }
    options?.onUpdate?.(task, Math.round((Date.now() - start) / 1000))
    if (task.status === 'done') return task
    if (task.status === 'failed') throw new Error(task.error || '任务执行失败')
    if (Date.now() - start > timeout) throw new Error('任务超时，请稍后在任务中心查看')
    await new Promise((resolve) => setTimeout(resolve, interval))
  }
}

/** 从任务/资产数据中安全取出 result.asset_ids */
export function taskAssetIds(task: StudioTask): number[] {
  const result = parseMaybeJson<{ asset_ids?: number[] }>(task.result)
  return Array.isArray(result.asset_ids) ? result.asset_ids : []
}

// ---------- 对话工作台 ----------

/** 会话列表 */
export function listChatSessions() {
  return request.get<BaseResponse<ChatSession[]>>({ url: '/api/chat/sessions' })
}

/** 会话历史消息 */
export function listChatMessages(sessionId: number) {
  return request.get<BaseResponse<ChatMessage[]>>({
    url: '/api/chat/messages',
    params: { session_id: sessionId }
  })
}

/** 发送消息：AI 编排（生图/抠图/查询） */
export function sendChat(data: { message: string; session_id?: number }) {
  return request.post<BaseResponse<ChatSendResult>>({ url: '/api/chat', data, timeout: 60000 })
}

/** 快捷指令 */
export function getQuickCommands() {
  return request.get<BaseResponse<QuickCommand[]>>({ url: '/api/chat/quick-commands' })
}

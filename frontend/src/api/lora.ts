/**
 * LoRA 训练 API 封装
 *
 * - 数据集管理：后端直连文件系统（docker 卷 data/lora_datasets）
 * - 训练控制：后端代理宿主机助手（训练跑在宿主机 GPU），失败时返回 fail(502)
 */
import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

// ---------- 类型定义 ----------

/** 数据集条目（目录即数据集，count 为样本图片数） */
export interface LoraDataset {
  name: string
  count: number
  updated_at: string
}

/** 训练环境单项检查结果 */
export interface TrainEnvItem {
  name: string
  ok: boolean
  detail: string
}

/** 训练环境检测结果 */
export interface TrainEnv {
  ready: boolean
  items: TrainEnvItem[]
}

/** 训练状态（宿主机助手透传） */
export interface TrainStatus {
  running: boolean
  pid: number | null
  log_tail: string
  message?: string
}

// ---------- 数据集管理 ----------

/** 数据集列表 */
export function listLoraDatasets() {
  return request.get<BaseResponse<LoraDataset[]>>({ url: '/api/lora/datasets' })
}

/** 创建数据集（目录） */
export function createLoraDataset(name: string) {
  return request.post<BaseResponse<{ name: string; created: boolean }>>({
    url: '/api/lora/datasets',
    data: { name }
  })
}

/** 删除数据集（整目录删除，不可恢复） */
export function deleteLoraDataset(name: string) {
  return request.del<BaseResponse<{ deleted: boolean }>>({ url: `/api/lora/datasets/${name}` })
}

/** 多图上传入数据集（multipart，字段名 files） */
export function uploadLoraImages(name: string, files: File[]) {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  return request.post<BaseResponse<{ saved: number }>>({
    url: `/api/lora/datasets/${name}/upload`,
    data: form,
    timeout: 120000
  })
}

/** 删除数据集内一张样本图 */
export function deleteLoraImage(name: string, filename: string) {
  return request.del<BaseResponse<{ deleted: boolean }>>({
    url: `/api/lora/datasets/${name}/images/${filename}`
  })
}

// ---------- 训练控制（代理宿主机助手） ----------

/** 训练环境检测（/train/env 代理） */
export function getLoraEnv() {
  return request.get<BaseResponse<TrainEnv>>({ url: '/api/lora/env', timeout: 15000 })
}

/** 开始训练（/train/start 代理，token 由后端附加） */
export function startLoraTrain(data: { dataset: string; trigger: string }) {
  return request.post<BaseResponse<{ ok: boolean; message: string }>>({
    url: '/api/lora/train',
    data,
    timeout: 30000
  })
}

/** 停止训练（/train/stop 代理，按 PID 终止） */
export function stopLoraTrain(dataset: string) {
  return request.post<BaseResponse<{ ok: boolean; message: string }>>({
    url: '/api/lora/train/stop',
    data: { dataset },
    timeout: 30000
  })
}

/** 训练状态（/train/status 代理：running + 日志尾部 60 行） */
export function getLoraTrainStatus(dataset: string) {
  return request.get<BaseResponse<TrainStatus>>({
    url: '/api/lora/train/status',
    params: { dataset }
  })
}

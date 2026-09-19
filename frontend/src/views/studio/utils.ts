/**
 * AI Images Studio 页面通用逻辑
 * 提供轮询 hook、资产/任务类型元信息、缩略图地址处理等公共能力
 */
import { ref, onUnmounted } from 'vue'
import {
  getAsset,
  listAssets,
  pollTask,
  taskAssetIds,
  StudioAsset,
  StudioTask
} from '@/api/studio'

/** 任务状态 → 中文文案 */
export const TASK_STATUS_TEXT: Record<string, string> = {
  queued: '排队中',
  running: '运行中',
  done: '已完成',
  failed: '失败'
}

/** 任务/资产类型 → 中文文案 */
export const TASK_TYPE_TEXT: Record<string, string> = {
  generate: '生图',
  matting: '抠图',
  upload: '上传'
}

/** 任务状态 → Element Plus tag 类型 */
export const TASK_STATUS_TAG: Record<string, 'info' | 'primary' | 'success' | 'danger'> = {
  queued: 'info',
  running: 'primary',
  done: 'success',
  failed: 'danger'
}

/** 资产类型 → badge 样式类 */
export const ASSET_BADGE_CLASS: Record<string, string> = {
  generate: 'asset-badge generate',
  matting: 'asset-badge matting',
  upload: 'asset-badge upload'
}

/**
 * 轮询指定任务，done 时按 asset_ids 拉取产物资产
 * 返回 null 表示已卸载或失败
 */
export function useTaskPolling() {
  const polling = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  const stop = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    polling.value = false
  }

  onUnmounted(stop)

  const poll = async (
    taskId: number,
    onDone: (assets: StudioAsset[], task: StudioTask) => void,
    onError?: (msg: string) => void
  ) => {
    polling.value = true
    try {
      const task = await pollTask(taskId, { onUpdate: () => undefined })
      const ids = taskAssetIds(task)
      const assets: StudioAsset[] = []
      for (const id of ids) {
        const res = await getAsset(id)
        if (res.data) assets.push(res.data)
      }
      if (polling.value) onDone(assets, task)
    } catch (error) {
      onError?.(error instanceof Error ? error.message : '任务执行失败')
    } finally {
      stop()
    }
  }

  return { polling, poll, stop }
}

/** 拉取最近若干资产（按类型过滤） */
export async function fetchRecentAssets(type?: string, pageSize = 12): Promise<StudioAsset[]> {
  const res = await listAssets({ type, page: 1, page_size: pageSize })
  return res.data?.items ?? []
}

/** 从 asset id 列表批量拉取资产详情 */
export async function fetchAssetsByIds(ids: number[]): Promise<StudioAsset[]> {
  const assets: StudioAsset[] = []
  for (const id of ids) {
    try {
      const res = await getAsset(id)
      if (res.data) assets.push(res.data)
    } catch {
      // 单个资产拉取失败不影响整体渲染
    }
  }
  return assets
}

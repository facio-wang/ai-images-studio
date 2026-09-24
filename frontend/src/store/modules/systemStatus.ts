import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ComfyStartResult, getSystemStatus, startComfyUI, SystemStatus } from '@/api/studio'

const POLL_INTERVAL = 30000

/**
 * 生图服务（ComfyUI）状态：全局共享的轮询与一键启动。
 * 顶栏状态按钮 / 工作台服务状态条 / 对话页横幅共用同一个轮询器与启动动作，
 * 避免各页面各自起定时器重复请求。
 */
export const useSystemStatusStore = defineStore(
  'systemStatusStore',
  () => {
    const status = ref<SystemStatus | null>(null)
    /** 一键启动进行中：按钮 loading 与启动耗时展示共用 */
    const starting = ref(false)
    /** 启动已等待秒数（前端计时，与后端探活互相印证） */
    const startElapsed = ref(0)

    let pollTimer: ReturnType<typeof setInterval> | null = null
    let pollerCount = 0
    let elapsedTimer: ReturnType<typeof setInterval> | null = null

    const running = computed(() => status.value?.comfyui.status === 'running')
    /** 服务已确认离线（status 尚未拉到时不算，避免页面加载时横幅闪现） */
    const serviceDown = computed(() => status.value !== null && status.value.comfyui.status !== 'running')

    /** 拉取一次状态；失败时保留上次值，面板与横幅不闪断 */
    async function fetchStatus() {
      try {
        const res = await getSystemStatus()
        status.value = res.data
      } catch {
        // 探测失败保持上次状态
      }
    }

    /** 共享轮询：多组件订阅时只保留一个定时器 */
    function startPolling() {
      pollerCount++
      if (!pollTimer) pollTimer = setInterval(fetchStatus, POLL_INTERVAL)
    }

    function stopPolling() {
      pollerCount = Math.max(0, pollerCount - 1)
      if (pollerCount === 0 && pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }

    /** 一键启动：后端拉起脚本并阻塞探活，返回后立即刷新状态并按结果提示 */
    async function startService(): Promise<ComfyStartResult | null> {
      if (starting.value) return null
      starting.value = true
      startElapsed.value = 0
      elapsedTimer = setInterval(() => startElapsed.value++, 1000)
      try {
        const res = await startComfyUI()
        const result = res.data
        if (result) {
          if (result.status === 'started' || result.status === 'already_running') {
            ElMessage.success(result.message)
          } else {
            ElMessage.warning(result.message)
          }
        }
        await fetchStatus()
        return result
      } catch {
        // 请求层已统一弹错误提示
        return null
      } finally {
        if (elapsedTimer) clearInterval(elapsedTimer)
        starting.value = false
      }
    }

    return { status, starting, startElapsed, running, serviceDown, fetchStatus, startPolling, stopPolling, startService }
  }
)

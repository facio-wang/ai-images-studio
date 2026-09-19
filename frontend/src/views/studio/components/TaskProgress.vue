<!-- 任务等待进度：平滑进度条 + 已用时长 + 阶段说明（低配设备友好，不精确到真实步数） -->
<template>
  <div class="task-progress">
    <div class="tp-head">
      <span class="tp-dot" aria-hidden="true"></span>
      <span class="tp-phase">{{ phaseText }}</span>
    </div>
    <ElProgress :percentage="display" :stroke-width="8" :show-text="false" class="tp-bar" />
    <div class="tp-meta">
      <span>已等待 {{ elapsedText }}</span>
      <span v-if="hint" class="tp-hint">{{ hint }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    /** 目标百分比（0~100），组件内部平滑逼近，避免进度条跳跃 */
    percent: number
    /** 已等待秒数 */
    elapsedSec: number
    /** 阶段文案（排队/推理中/生图中…） */
    phaseText: string
    /** 弱提示（如"低配设备可能需要几分钟"） */
    hint?: string
  }>(),
  {}
)

const display = ref(0)
let animTimer: ReturnType<typeof setInterval> | null = null

// 显示值每 200ms 向目标缓动逼近 8%，观感平滑
watch(
  () => props.percent,
  () => {
    if (animTimer) return
    animTimer = setInterval(() => {
      const delta = props.percent - display.value
      if (Math.abs(delta) < 0.5) {
        display.value = props.percent
        if (animTimer) {
          clearInterval(animTimer)
          animTimer = null
        }
        return
      }
      display.value = Math.min(100, display.value + delta * 0.08)
    }, 200)
  },
  { immediate: true }
)

onUnmounted(() => {
  if (animTimer) clearInterval(animTimer)
})

const elapsedText = computed(() => {
  const s = Math.max(0, props.elapsedSec)
  if (s < 60) return `${s}s`
  return `${Math.floor(s / 60)}m ${s % 60}s`
})
</script>

<style lang="scss" scoped>
  .task-progress {
    max-width: 420px;
    margin: 0 auto;
    padding: 28px 0;

    .tp-head {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      font-size: 13px;
      font-weight: 600;
      color: var(--art-text-gray-900);

      .tp-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--art-primary);
        animation: tp-pulse 1.4s ease infinite;
      }
    }

    .tp-meta {
      display: flex;
      justify-content: space-between;
      margin-top: 8px;
      font-size: 11px;
      color: var(--art-gray-500);

      .tp-hint {
        color: var(--art-gray-400, #98a2b3);
      }
    }
  }

  @keyframes tp-pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.35;
    }
  }
</style>

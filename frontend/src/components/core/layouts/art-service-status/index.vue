<!-- 顶栏生图服务状态：状态点 + 弹出详情面板（一键启动 / 刷新 / 资源概览），全局公共区域入口 -->
<template>
  <el-popover
    placement="bottom-end"
    :width="330"
    trigger="click"
    :show-arrow="false"
    :hide-after="0"
    popper-style="padding: 14px 16px; border: 1px solid var(--art-border-dashed-color); border-radius: calc(var(--custom-radius) / 2 + 4px);"
  >
    <template #reference>
      <div class="svc-wrap">
        <div class="svc-trigger" title="生图服务（ComfyUI）状态">
          <span class="svc-dot" :class="dotClass"></span>
          <span class="svc-trigger-text">生图服务</span>
        </div>
      </div>
    </template>

    <div class="svc-panel">
      <div class="svc-head">
        <span class="svc-title">
          <span class="svc-dot" :class="dotClass"></span>
          生图服务（ComfyUI）
        </span>
        <i class="iconfont-sys svc-refresh" :class="{ spinning: refreshing }" title="刷新状态" @click="refresh">
          &#xe6b3;
        </i>
      </div>

      <template v-if="comfy">
        <div class="svc-row">
          <span class="k">状态</span>
          <span class="v" :class="running ? 'ok' : 'down'">{{ running ? '运行中' : '未启动' }}</span>
        </div>
        <div class="svc-row">
          <span class="k">地址</span>
          <span class="v mono">{{ comfy.url }}</span>
        </div>
        <template v-if="running">
          <div class="svc-row">
            <span class="k">版本</span>
            <span class="v">{{ comfy.version || '—' }}</span>
          </div>
          <div class="svc-row">
            <span class="k">队列</span>
            <span class="v">运行 {{ comfy.queue_running }} · 排队 {{ comfy.queue_pending }}</span>
          </div>
          <div v-for="(d, i) in comfy.devices" :key="i" class="svc-row">
            <span class="k">GPU</span>
            <span class="v">{{ d.name || '—' }} · 空闲 {{ fmtMB(d.vram_free_mb) }} / {{ fmtMB(d.vram_total_mb) }}</span>
          </div>
        </template>
        <p v-else class="svc-warn">
          生图/对话生图功能暂不可用。可一键拉起启动脚本（需后端与 ComfyUI 同机），或在 Win11 宿主机手动启动。
        </p>
        <ElButton
          v-if="!running"
          class="svc-start"
          type="primary"
          size="small"
          :loading="starting"
          @click="start"
        >
          {{ starting ? `启动中 ${startElapsed}s…` : '⚡ 一键启动' }}
        </ElButton>
      </template>
      <p v-else class="svc-warn">正在检测服务状态…</p>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
  import { computed, ref } from 'vue'
  import { useSystemStatusStore } from '@/store/modules/systemStatus'

  defineOptions({ name: 'ArtServiceStatus' })

  const sysStore = useSystemStatusStore()
  const refreshing = ref(false)

  const running = computed(() => sysStore.running)
  const starting = computed(() => sysStore.starting)
  const startElapsed = computed(() => sysStore.startElapsed)
  const comfy = computed(() => sysStore.status?.comfyui)

  const dotClass = computed(() => {
    if (starting.value) return 'starting'
    if (!sysStore.status) return 'unknown'
    return running.value ? 'running' : 'down'
  })

  const refresh = async () => {
    refreshing.value = true
    await sysStore.fetchStatus()
    refreshing.value = false
  }

  const start = () => sysStore.startService()

  const fmtMB = (v?: number | null) => (v == null || Number.isNaN(v) ? '—' : `${Math.round(v)} MB`)
</script>

<style lang="scss" scoped>
  .svc-wrap {
    display: flex;
    align-items: center;
    height: 60px; // 与顶栏 .btn-box 同高：顶栏 .right 为默认 stretch 对齐，靠自身高度实现垂直居中
    padding: 0 4px;
  }

  .svc-trigger {
    display: flex;
    align-items: center;
    gap: 7px;
    height: 38px;
    padding: 0 12px;
    cursor: pointer;
    user-select: none;
    border-radius: 6px;
    transition: background-color 0.2s;

    &:hover {
      background: rgba(128, 128, 128, 0.12);
    }

    .svc-trigger-text {
      font-size: 13px;
      font-weight: 500;
      color: var(--art-gray-600);
      white-space: nowrap;
    }
  }

  .svc-dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    flex-shrink: 0;
    border-radius: 50%;
    background: #c0c4cc;

    &.running {
      background: #34d399;
      box-shadow: 0 0 6px #34d39988;
    }

    &.down {
      background: #f87171;
      box-shadow: 0 0 6px #f8717188;
      animation: svc-pulse 1.6s ease-in-out infinite;
    }

    &.starting {
      background: #fbbf24;
      box-shadow: 0 0 6px #fbbf2488;
      animation: svc-pulse 1s ease-in-out infinite;
    }
  }

  @keyframes svc-pulse {
    50% {
      opacity: 0.35;
    }
  }

  .svc-panel {
    color: var(--art-text-gray-900);

    .svc-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;

      .svc-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 600;
      }

      .svc-refresh {
        padding: 4px;
        font-size: 15px;
        color: var(--art-gray-500);
        cursor: pointer;
        border-radius: 4px;
        transition: background-color 0.2s;

        &:hover {
          background: rgba(128, 128, 128, 0.12);
        }

        &.spinning {
          animation: svc-spin 0.8s linear infinite;
        }
      }
    }

    .svc-row {
      display: flex;
      gap: 10px;
      font-size: 12.5px;
      line-height: 1.9;

      .k {
        width: 42px;
        flex-shrink: 0;
        color: var(--art-gray-500);
      }

      .v {
        color: var(--art-text-gray-900);
        word-break: break-all;

        &.ok {
          font-weight: 600;
          color: #10b981;
        }

        &.down {
          font-weight: 600;
          color: #f87171;
        }

        &.mono {
          font-family: Consolas, Monaco, monospace;
          font-size: 12px;
        }
      }
    }

    .svc-warn {
      margin: 8px 0 10px;
      font-size: 12px;
      line-height: 1.6;
      color: #fbbf24;
    }

    .svc-start {
      width: 100%;
    }
  }

  @keyframes svc-spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>

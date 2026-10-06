<!-- 工作台概览：统计卡 + 最近资产网格 + 快捷入口 -->
<template>
  <div class="studio-page home-page">
    <div class="studio-header">
      <div>
        <h1>{{ $t('studio.home.title') }}</h1>
        <p class="desc">{{ $t('studio.home.desc', { n: todayTasks }) }}</p>
      </div>
      <div class="header-actions">
        <ElButton @click="openGuide">{{ $t('studio.home.replayGuide') }}</ElButton>
        <ElButton @click="$router.push('/manage/help')">{{ $t('studio.home.helpCenter') }}</ElButton>
        <ElButton @click="$router.push('/manage/tasks')">{{ $t('studio.home.taskCenter') }}</ElButton>
        <ElButton type="primary" @click="$router.push('/creation/generate')">{{ $t('studio.home.startGenerate') }}</ElButton>
      </div>
    </div>

    <!-- 统计卡 -->
    <div class="stat-grid">
      <div class="studio-card stat-card gradient">
        <div class="stat-label">{{ $t('studio.home.stat.todayTasks') }}</div>
        <div class="stat-num">{{ todayTasks }}</div>
        <div class="stat-sub">{{ $t('studio.home.stat.todayTasksSub') }}</div>
      </div>
      <div class="studio-card stat-card">
        <div class="stat-label">{{ $t('studio.home.stat.assetTotal') }}</div>
        <div class="stat-num cyan">{{ assetTotal }}</div>
        <div class="stat-sub">{{ $t(TASK_TYPE_KEY['generate']) }} {{ typeCount('generate') }} · {{ $t(TASK_TYPE_KEY['matting']) }} {{ typeCount('matting') }} · {{ $t(TASK_TYPE_KEY['upload']) }} {{ typeCount('upload') }}</div>
      </div>
      <div class="studio-card stat-card">
        <div class="stat-label">{{ $t('studio.home.stat.activeTasks') }}</div>
        <div class="stat-num purple">{{ activeTasks }}</div>
        <div class="stat-sub">{{ $t('studio.home.stat.activeTasksSub') }}</div>
      </div>
    </div>

    <!-- 系统状态（移植自 webUI-v1.0：生图服务状态 + GPU/内存资源仪表） -->
    <div class="system-bar studio-card">
      <div class="svc-status" :class="sysStatus?.comfyui.status">
        <span class="svc-dot"></span>
        <span class="svc-text">
          {{ $t('studio.common.service.fullName') }}
          {{ running ? $t('studio.common.service.running') : $t('studio.common.service.stopped') }}
        </span>
        <span v-if="running" class="svc-meta">
          v{{ sysStatus?.comfyui.version || '?' }} · {{ $t('studio.common.service.queue') }} {{ sysStatus?.comfyui.queue_running }}/{{ sysStatus?.comfyui.queue_pending }}
        </span>
        <ElButton
          v-if="running"
          size="small"
          type="danger"
          plain
          :loading="stopping"
          :title="$t('studio.common.service.stopTip')"
          @click="confirmStop"
        >
          {{ $t('studio.common.service.stopBtn') }}
        </ElButton>
        <template v-else>
          <span class="svc-meta warn">{{ $t('studio.common.service.manualHint') }}</span>
          <ElButton size="small" type="primary" plain :loading="starting" @click="startService">
            {{ starting ? $t('studio.common.service.startingBtn', { n: startElapsed }) : $t('studio.common.service.startBtn') }}
          </ElButton>
        </template>
      </div>
      <div class="res-meters">
        <div
          v-for="(d, di) in sysStatus?.comfyui.devices ?? []"
          :key="di"
          class="res-item"
          :title="`${d.name || ''} · ${d.torch_version || ''}`"
        >
          <span class="res-lab">{{ $t('studio.home.vramLabel') }}</span>
          <div class="meter">
            <i :style="{ width: meterPct(d.vram_total_mb ? 1 - (d.vram_free_mb ?? d.vram_total_mb) / d.vram_total_mb : 0) }"></i>
          </div>
          <span class="res-val">
            {{ fmtMB((d.vram_total_mb ?? 0) - (d.vram_free_mb ?? d.vram_total_mb ?? 0)) }} / {{ fmtMB(d.vram_total_mb) }}
          </span>
        </div>
        <div v-if="sysStatus?.comfyui.ram_total_mb" class="res-item">
          <span class="res-lab">{{ $t('studio.home.ramLabel') }}</span>
          <div class="meter"><i :style="{ width: meterPct(1 - (sysStatus.comfyui.ram_free_mb ?? 0) / sysStatus.comfyui.ram_total_mb) }"></i></div>
          <span class="res-val">
            {{ fmtMB(sysStatus.comfyui.ram_total_mb - (sysStatus.comfyui.ram_free_mb ?? 0)) }} / {{ fmtMB(sysStatus.comfyui.ram_total_mb) }}
          </span>
        </div>
      </div>
    </div>

    <div class="home-grid">
      <!-- 最近资产 -->
      <div class="studio-card">
        <div class="card-title recent-head">
          {{ $t('studio.home.recentTitle') }}
          <ElButton link type="primary" @click="$router.push('/manage/assets')">{{ $t('studio.home.goAssets') }}</ElButton>
        </div>
        <div v-if="recentAssets.length" class="recent-grid">
          <div
            v-for="asset in recentAssets"
            :key="asset.id"
            class="studio-thumb recent-item"
            :class="{ checker: asset.type === 'matting' }"
          >
            <ElImage
              :src="asset.thumb_url"
              :preview-src-list="[asset.url]"
              preview-teleported
              loading="lazy"
              :alt="asset.labels || ''"
              fit="cover"
              class="thumb-img"
            />
          </div>
        </div>
        <div v-else class="studio-empty"><span>{{ $t('studio.home.emptyRecent') }}</span></div>
      </div>

      <!-- 快捷入口 -->
      <div class="studio-card">
        <div class="card-title">{{ $t('studio.home.quickLinks') }}</div>
        <div class="entry-grid">
          <div class="entry-card" @click="$router.push('/creation/chat')">
            <div class="entry-icon">💬</div>
            <div class="entry-name">{{ $t('studio.home.entry.chat.name') }}</div>
            <div class="entry-sub">{{ $t('studio.home.entry.chat.sub') }}</div>
          </div>
          <div class="entry-card" @click="$router.push('/creation/generate')">
            <div class="entry-icon">🎨</div>
            <div class="entry-name">{{ $t('studio.home.entry.generate.name') }}</div>
            <div class="entry-sub">{{ $t('studio.home.entry.generate.sub') }}</div>
          </div>
          <div class="entry-card" @click="$router.push('/creation/matting')">
            <div class="entry-icon">✂️</div>
            <div class="entry-name">{{ $t('studio.home.entry.matting.name') }}</div>
            <div class="entry-sub">u2net / bria-rmbg</div>
          </div>
          <div class="entry-card" @click="$router.push('/manage/models')">
            <div class="entry-icon">🧠</div>
            <div class="entry-name">{{ $t('studio.home.entry.models.name') }}</div>
            <div class="entry-sub">{{ $t('studio.home.entry.models.sub') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 首次访问引导（ref 记忆键之外，可手动重放） -->
    <OnboardingGuide ref="guideRef" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { listAssets, listTasks, StudioAsset, StudioTask } from '@/api/studio'
import { useSystemStatusStore } from '@/store/modules/systemStatus'
import OnboardingGuide from './components/OnboardingGuide.vue'
import { TASK_TYPE_KEY } from './utils'
import './style.scss'

defineOptions({ name: 'StudioHome' })

const guideRef = ref<InstanceType<typeof OnboardingGuide>>()
const openGuide = () => guideRef.value?.open()

/** 生图服务状态：全局共享 store（顶栏/对话页/工作台共用一个轮询器） */
const { t } = useI18n()
const sysStore = useSystemStatusStore()
const { status: sysStatus, running, starting, stopping, startElapsed } = storeToRefs(sysStore)
const startService = () => sysStore.startService()

/** 停止服务前二次确认（中断任务/释放显存是破坏性动作） */
const confirmStop = async () => {
  try {
    await ElMessageBox.confirm(
      t('studio.common.service.stopConfirm'),
      t('studio.common.service.stopConfirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('studio.common.service.stopBtn'),
        cancelButtonText: t('studio.common.actions.cancel')
      }
    )
  } catch {
    return
  }
  sysStore.stopService()
}

const todayTasks = ref(0)
const activeTasks = ref(0)
const assetTotal = ref(0)
const typeCounts = ref<Record<string, number>>({})
const recentAssets = ref<StudioAsset[]>([])

const meterPct = (ratio: number | null | undefined) =>
  `${Math.round(Math.min(1, Math.max(0, ratio ?? 0)) * 100)}%`

const fmtMB = (v?: number | null) => (v == null || Number.isNaN(v) ? '—' : `${Math.round(v)} MB`)

const typeCount = (type: string) => typeCounts.value[type] ?? 0

/** 统计数据从任务/资产列表计算 */
const loadStats = async () => {
  try {
    const [taskRes, assetRes] = await Promise.all([listTasks({ limit: 200 }), listAssets({ page: 1, page_size: 1 })])
    const tasks: StudioTask[] = taskRes.data ?? []
    const today = new Date().toDateString()
    todayTasks.value = tasks.filter((t) => new Date(t.created_at).toDateString() === today).length
    activeTasks.value = tasks.filter((t) => t.status === 'queued' || t.status === 'running').length
    assetTotal.value = assetRes.data?.total ?? 0
  } catch {
    // 统计失败保持 0
  }
}

/** 各类型资产数：按类型分别取 total */
const loadTypeCounts = async () => {
  const counts: Record<string, number> = {}
  await Promise.all(
    ['generate', 'matting', 'upload'].map(async (type) => {
      try {
        const res = await listAssets({ type, page: 1, page_size: 1 })
        counts[type] = res.data?.total ?? 0
      } catch {
        counts[type] = 0
      }
    })
  )
  typeCounts.value = counts
}

const loadRecent = async () => {
  try {
    const res = await listAssets({ page: 1, page_size: 6 })
    recentAssets.value = res.data?.items ?? []
  } catch {
    // 最近作品失败不阻塞概览
  }
}

onMounted(() => {
  loadStats()
  loadTypeCounts()
  loadRecent()
  sysStore.fetchStatus()
  sysStore.startPolling()
})

onUnmounted(() => {
  sysStore.stopPolling()
})
</script>

<style lang="scss" scoped>
  .header-actions {
    display: flex;
    gap: 10px;
  }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 16px;
  }

  .stat-card.gradient {
    background: linear-gradient(135deg, var(--art-main-bg-color) 60%, rgba(37, 99, 235, 0.12));
  }

  .stat-label {
    font-size: 12px;
    color: var(--art-gray-600);
    margin-bottom: 4px;
  }

  .stat-num {
    font-size: 30px;
    font-weight: 800;
    color: #60a5fa;

    &.cyan {
      color: #22d3ee;
    }

    &.purple {
      color: #a78bfa;
    }
  }

  .stat-sub {
    margin-top: 4px;
    font-size: 11px;
    color: var(--art-gray-500);
  }

  .system-bar {
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
    padding: 12px 16px;
    margin-bottom: 16px;

    .svc-status {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12.5px;
      font-weight: 600;

      .svc-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #f87171;
        box-shadow: 0 0 6px #f8717188;
      }

      &.running .svc-dot {
        background: #34d399;
        box-shadow: 0 0 6px #34d39988;
      }
    }

    .svc-meta {
      font-weight: 400;
      font-size: 11.5px;
      color: var(--art-gray-500);

      &.warn {
        color: #fbbf24;
      }
    }

    .res-meters {
      display: flex;
      gap: 24px;
      flex: 1;
      min-width: 0;
    }

    .res-item {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 240px;
      flex: 1;

      .res-lab {
        font-size: 11.5px;
        color: var(--art-gray-500);
        white-space: nowrap;
      }

      .meter {
        flex: 1;
        height: 6px;
        border-radius: 3px;
        background: var(--art-gray-200);
        overflow: hidden;

        i {
          display: block;
          height: 100%;
          border-radius: 3px;
          background: linear-gradient(90deg, #2563eb, #06b6d4);
        }
      }

      .res-val {
        font-size: 11px;
        color: var(--art-gray-600);
        white-space: nowrap;
      }
    }
  }

  .home-grid {
    display: grid;
    grid-template-columns: minmax(0, 8fr) minmax(280px, 4fr);
    gap: 16px;
    align-items: start;
  }

  .recent-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .recent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 10px;
  }

  .recent-item {
    aspect-ratio: 1;
    border-radius: 6px;
  }

  /* ElImage 铺满缩略容器，点击打开大图查看器 */
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

  .entry-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .entry-card {
    padding: 14px;
    border: 1px solid var(--art-border-dashed-color);
    border-radius: 6px;
    cursor: pointer;
    transition: border-color 0.15s;

    &:hover {
      border-color: var(--art-primary);
    }

    .entry-icon {
      font-size: 20px;
      margin-bottom: 4px;
    }

    .entry-name {
      font-size: 12px;
      font-weight: 600;
      color: var(--art-text-gray-900);
    }

    .entry-sub {
      font-size: 10.5px;
      color: var(--art-gray-500);
      margin-top: 2px;
    }
  }
</style>

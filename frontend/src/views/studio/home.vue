<!-- 工作台概览：统计卡 + 最近资产网格 + 快捷入口 -->
<template>
  <div class="studio-page home-page">
    <div class="studio-header">
      <div>
        <h1>工作台</h1>
        <p class="desc">本地 AI 创作中台 · 今天已提交 {{ todayTasks }} 个任务</p>
      </div>
      <div class="header-actions">
        <ElButton @click="openGuide">📖 重新查看引导</ElButton>
        <ElButton @click="$router.push('/manage/help')">帮助中心</ElButton>
        <ElButton @click="$router.push('/manage/tasks')">📋 任务中心</ElButton>
        <ElButton type="primary" @click="$router.push('/creation/generate')">🎨 开始生图</ElButton>
      </div>
    </div>

    <!-- 统计卡 -->
    <div class="stat-grid">
      <div class="studio-card stat-card gradient">
        <div class="stat-label">今日任务数</div>
        <div class="stat-num">{{ todayTasks }}</div>
        <div class="stat-sub">含生图与抠图任务</div>
      </div>
      <div class="studio-card stat-card">
        <div class="stat-label">资产总数</div>
        <div class="stat-num cyan">{{ assetTotal }}</div>
        <div class="stat-sub">生图 {{ typeCount('generate') }} · 抠图 {{ typeCount('matting') }} · 上传 {{ typeCount('upload') }}</div>
      </div>
      <div class="studio-card stat-card">
        <div class="stat-label">排队 / 运行中</div>
        <div class="stat-num purple">{{ activeTasks }}</div>
        <div class="stat-sub">进行中任务完成后自动入资产库</div>
      </div>
    </div>

    <!-- 系统状态（移植自 webUI-v1.0：生图服务状态 + GPU/内存资源仪表） -->
    <div class="system-bar studio-card">
      <div class="svc-status" :class="sysStatus?.comfyui.status">
        <span class="svc-dot"></span>
        <span class="svc-text">
          生图服务（ComfyUI）
          {{ sysStatus?.comfyui.status === 'running' ? '运行中' : '未启动' }}
        </span>
        <span v-if="sysStatus?.comfyui.status === 'running'" class="svc-meta">
          v{{ sysStatus.comfyui.version || '?' }} · 队列 {{ sysStatus.comfyui.queue_running }}/{{ sysStatus.comfyui.queue_pending }}
        </span>
        <span v-else class="svc-meta warn">生图/对话生图功能暂不可用，请在 Win11 宿主机启动 ComfyUI（端口 8188）</span>
      </div>
      <div class="res-meters">
        <div
          v-for="(d, di) in sysStatus?.comfyui.devices ?? []"
          :key="di"
          class="res-item"
          :title="`${d.name || ''} · ${d.torch_version || ''}`"
        >
          <span class="res-lab">GPU 显存</span>
          <div class="meter">
            <i :style="{ width: meterPct(d.vram_total_mb ? 1 - (d.vram_free_mb ?? d.vram_total_mb) / d.vram_total_mb : 0) }"></i>
          </div>
          <span class="res-val">
            {{ fmtMB((d.vram_total_mb ?? 0) - (d.vram_free_mb ?? d.vram_total_mb ?? 0)) }} / {{ fmtMB(d.vram_total_mb) }}
          </span>
        </div>
        <div v-if="sysStatus?.comfyui.ram_total_mb" class="res-item">
          <span class="res-lab">系统内存</span>
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
          最近作品
          <ElButton link type="primary" @click="$router.push('/manage/assets')">进入资产库 →</ElButton>
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
        <div v-else class="studio-empty"><span>还没有作品，从生图或对话工作台开始吧</span></div>
      </div>

      <!-- 快捷入口 -->
      <div class="studio-card">
        <div class="card-title">快捷入口</div>
        <div class="entry-grid">
          <div class="entry-card" @click="$router.push('/creation/chat')">
            <div class="entry-icon">💬</div>
            <div class="entry-name">对话工作台</div>
            <div class="entry-sub">一句话完成处理</div>
          </div>
          <div class="entry-card" @click="$router.push('/creation/generate')">
            <div class="entry-icon">🎨</div>
            <div class="entry-name">新建生图</div>
            <div class="entry-sub">ComfyUI 文生图</div>
          </div>
          <div class="entry-card" @click="$router.push('/creation/matting')">
            <div class="entry-icon">✂️</div>
            <div class="entry-name">抠图工具箱</div>
            <div class="entry-sub">u2net / bria-rmbg</div>
          </div>
          <div class="entry-card" @click="$router.push('/manage/models')">
            <div class="entry-icon">🧠</div>
            <div class="entry-name">模型中心</div>
            <div class="entry-sub">底模 / LoRA / 翻译</div>
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
import { getSystemStatus, listAssets, listTasks, StudioAsset, StudioTask, SystemStatus } from '@/api/studio'
import OnboardingGuide from './components/OnboardingGuide.vue'
import './style.scss'

defineOptions({ name: 'StudioHome' })

const guideRef = ref<InstanceType<typeof OnboardingGuide>>()
const openGuide = () => guideRef.value?.open()

const todayTasks = ref(0)
const activeTasks = ref(0)
const assetTotal = ref(0)
const typeCounts = ref<Record<string, number>>({})
const recentAssets = ref<StudioAsset[]>([])
const sysStatus = ref<SystemStatus | null>(null)
let sysTimer: ReturnType<typeof setInterval> | null = null

/** 系统状态：ComfyUI 连通性 + GPU/内存（30s 轮询，移植自 webUI-v1.0） */
const loadSystem = async () => {
  try {
    const res = await getSystemStatus()
    sysStatus.value = res.data
  } catch {
    // 状态获取失败保持上次值
  }
}

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
  loadSystem()
  sysTimer = setInterval(loadSystem, 30000)
})

onUnmounted(() => {
  if (sysTimer) clearInterval(sysTimer)
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

<!-- 系统设置：只读系统信息 + 关于卡（不含任何 key 编辑） -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>{{ $t('studio.settings.title') }}</h1>
        <p class="desc">{{ $t('studio.settings.desc') }}</p>
      </div>
      <ElButton @click="load">{{ $t('studio.settings.refresh') }}</ElButton>
    </div>

    <div class="settings-layout">
      <!-- 运行信息 -->
      <div class="studio-card">
        <div class="card-title">{{ $t('studio.settings.runInfo') }}</div>
        <ElDescriptions :column="1" border>
          <ElDescriptionsItem :label="$t('studio.settings.app')">{{ meta?.name ?? '—' }}</ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('studio.settings.version')">{{ meta?.version ?? '—' }}</ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('studio.settings.serviceUrl')">{{ host }}</ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('studio.settings.authMode')">{{ $t('studio.settings.authModeValue') }}</ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('studio.settings.dataDir')">{{ $t('studio.settings.dataDirValue') }}</ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('studio.settings.engine')">{{ $t('studio.settings.engineValue') }}</ElDescriptionsItem>
        </ElDescriptions>

        <!-- 本地运行设备（ComfyUI 上报的 GPU / 内存信息） -->
        <div class="card-title device-title">{{ $t('studio.settings.devices') }}</div>
        <ElTable
          :data="devices"
          size="small"
          class="device-table"
          :empty-text="status?.comfyui.status === 'stopped' ? $t('studio.settings.devicesOffline') : $t('studio.settings.devicesEmpty')"
        >
          <ElTableColumn prop="name" :label="$t('studio.settings.deviceName')" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="dev-name">{{ row.name || '—' }}</span>
            </template>
          </ElTableColumn>
          <ElTableColumn prop="type" :label="$t('studio.settings.deviceType')" width="90">
            <template #default="{ row }">
              <ElTag size="small" :type="row.type === 'cuda' ? 'success' : 'info'">{{ row.type || '—' }}</ElTag>
            </template>
          </ElTableColumn>
          <ElTableColumn prop="torch_version" :label="$t('studio.settings.torchVer')" width="130" show-overflow-tooltip>
            <template #default="{ row }">{{ row.torch_version || '—' }}</template>
          </ElTableColumn>
          <ElTableColumn :label="$t('studio.settings.vramTotal')" width="100" align="right">
            <template #default="{ row }">{{ fmtGb(row.vram_total_mb) }}</template>
          </ElTableColumn>
          <ElTableColumn :label="$t('studio.settings.vramFree')" width="100" align="right">
            <template #default="{ row }">{{ fmtGb(row.vram_free_mb) }}</template>
          </ElTableColumn>
          <ElTableColumn :label="$t('studio.settings.vramUsage')" min-width="160">
            <template #default="{ row }">
              <div class="vram-meter">
                <ElProgress :percentage="vramPct(row)" :stroke-width="8" :show-text="false" />
                <span class="v">{{ vramPct(row) }}%</span>
              </div>
            </template>
          </ElTableColumn>
        </ElTable>
        <div class="ram-line">
          {{ $t('studio.settings.ramLine', {
            free: fmtGb(status?.comfyui.ram_free_mb ?? null),
            total: fmtGb(status?.comfyui.ram_total_mb ?? null)
          }) }}
        </div>

        <div class="tip-block">
          {{ $t('studio.settings.secretTip') }}
        </div>
      </div>

      <!-- 关于 -->
      <div class="studio-card">
        <div class="card-title">{{ $t('studio.settings.about') }}</div>
        <div class="about-logo">AI</div>
        <h2 class="about-name">AI Images Studio</h2>
        <p class="about-desc">{{ $t('studio.settings.aboutDesc') }}</p>

        <ElDivider />

        <ul class="about-list">
          <li><b>{{ $t('studio.settings.versionLabel') }}</b>v0.1（P1）</li>
          <li><b>{{ $t('studio.settings.license') }}</b>GPL-3.0</li>
          <li><b>{{ $t('studio.settings.deploy') }}</b>{{ $t('studio.settings.deployValue') }}</li>
          <li><b>{{ $t('studio.settings.backend') }}</b>FastAPI + SQLite + ComfyUI</li>
          <li><b>{{ $t('studio.settings.frontend') }}</b>Vue3 + TS + Element Plus</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getSystemMeta, getSystemStatus, SystemMeta, SystemStatus } from '@/api/studio'
import './style.scss'

defineOptions({ name: 'StudioSettings' })

const meta = ref<SystemMeta | null>(null)
const status = ref<SystemStatus | null>(null)
// 模板中不能直接访问 window.location，提前取好
const host = window.location.host

/** ComfyUI 上报的本地计算设备列表（服务未启动时为空数组走空态） */
const devices = computed(() => status.value?.comfyui.devices ?? [])

/** MB → GB 文案（保留 1 位小数，未知显示 —） */
const fmtGb = (mb: number | null | undefined) =>
  mb == null ? '—' : `${(mb / 1024).toFixed(1)} GB`

const vramPct = (row: { vram_total_mb: number | null; vram_free_mb: number | null }) => {
  const total = row.vram_total_mb ?? 0
  if (total <= 0) return 0
  return Math.min(100, Math.round(((total - (row.vram_free_mb ?? 0)) / total) * 100))
}

const load = async () => {
  try {
    const res = await getSystemMeta()
    meta.value = res.data
  } catch {
    // 元信息加载失败时展示占位
  }
  try {
    const res = await getSystemStatus()
    status.value = res.data
  } catch {
    // 服务状态失败时设备表走空态
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
  .settings-layout {
    display: grid;
    grid-template-columns: minmax(0, 7fr) minmax(280px, 5fr);
    gap: 16px;
    align-items: start;
  }

  .device-title {
    margin-top: 18px;
  }

  .device-table {
    width: 100%;

    .dev-name {
      font-size: 12.5px;
      font-weight: 500;
    }

    .vram-meter {
      display: flex;
      align-items: center;
      gap: 8px;

      .el-progress {
        flex: 1;
      }

      .v {
        font-size: 11.5px;
        color: var(--art-gray-600);
        width: 36px;
        text-align: right;
      }
    }
  }

  .ram-line {
    margin-top: 8px;
    font-size: 12px;
    color: var(--art-gray-500);
  }

  .tip-block {
    margin-top: 14px;
    padding: 10px 14px;
    font-size: 12px;
    border-radius: 6px;
    color: #22d3ee;
    background: rgba(6, 182, 212, 0.08);
    border: 1px solid rgba(6, 182, 212, 0.3);
  }

  .about-logo {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: 800;
    color: #fff;
    border-radius: 6px;
    background: linear-gradient(135deg, #2563eb, #06b6d4);
  }

  .about-name {
    margin-top: 12px;
    font-size: 18px;
    font-weight: 700;
    color: var(--art-text-gray-900);
  }

  .about-desc {
    margin-top: 4px;
    font-size: 12px;
    color: var(--art-gray-600);
  }

  .about-list {
    list-style: none;
    padding: 0;
    margin: 0;

    li {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      font-size: 13px;
      border-bottom: 1px dashed var(--art-border-dashed-color);

      &:last-child {
        border-bottom: none;
      }

      b {
        color: var(--art-gray-500);
        font-weight: 400;
      }
    }
  }
</style>

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
import { onMounted, ref } from 'vue'
import { getSystemMeta, SystemMeta } from '@/api/studio'
import './style.scss'

defineOptions({ name: 'StudioSettings' })

const meta = ref<SystemMeta | null>(null)
// 模板中不能直接访问 window.location，提前取好
const host = window.location.host

const load = async () => {
  try {
    const res = await getSystemMeta()
    meta.value = res.data
  } catch {
    // 元信息加载失败时展示占位
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

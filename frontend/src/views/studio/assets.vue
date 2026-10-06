<!-- 资产库：类型筛选 + 卡片网格 + 删除/下载 + 存储概览 -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>{{ $t('studio.assets.title') }}</h1>
        <p class="desc">{{ $t('studio.assets.desc') }}</p>
      </div>
      <ElUpload :show-file-list="false" :auto-upload="false" accept="image/*" :on-change="onUpload">
        <ElButton type="primary" :loading="uploading">{{ $t('studio.assets.uploadBtn') }}</ElButton>
      </ElUpload>
    </div>

    <!-- 存储信息条 -->
    <div class="storage-bar studio-card" v-if="meta">
      <span>{{ $t('studio.assets.storageMeta', { name: meta.name, version: meta.version }) }}</span>
      <span class="divider">|</span>
      <span>{{ $t('studio.assets.totalCount', { n: total }) }}</span>
      <span class="divider">|</span>
      <span>{{ $t('studio.assets.currentFilter', { filter: activeTypeText }) }}</span>
    </div>

    <!-- 类型筛选 -->
    <div class="tabs-row">
      <div
        v-for="tab in typeTabs"
        :key="tab.key"
        class="tab-item"
        :class="{ on: activeType === tab.key }"
        @click="switchType(tab.key)"
      >
        {{ tab.label }}
      </div>
    </div>

    <div v-if="loading" class="studio-empty"><ElIcon class="is-loading" :size="22"><Loading /></ElIcon></div>

    <div v-else-if="assets.length" class="asset-grid">
      <div v-for="asset in assets" :key="asset.id" class="asset-card">
        <div class="studio-thumb asset-thumb" :class="{ checker: asset.type === 'matting' }">
          <ElImage
            :src="asset.thumb_url"
            :preview-src-list="[asset.url]"
            preview-teleported
            loading="lazy"
            :alt="asset.labels || asset.filename || ''"
            fit="cover"
            class="thumb-img"
          />
          <div class="thumb-ops">
            <ElButton size="small" @click.stop="showDetail(asset)">{{ $t('studio.common.actions.detail') }}</ElButton>
            <ElButton size="small" tag="a" :href="asset.url" target="_blank">⬇</ElButton>
            <ElButton size="small" type="danger" @click="remove(asset)">🗑</ElButton>
          </div>
        </div>
        <div class="asset-meta">
          <div class="asset-title">
            <span class="truncate">#{{ asset.id }} {{ asset.labels || asset.filename || $t('studio.assets.unnamed') }}</span>
          </div>
          <div class="asset-sub">
            <i :class="ASSET_BADGE_CLASS[asset.type]">{{ typeText(asset.type) }}</i>
            <span class="time">{{ formatTime(asset.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="studio-empty"><span>{{ $t('studio.assets.empty') }}</span></div>

    <div v-if="total > assets.length" class="load-more">
      <ElButton :loading="loading" @click="loadMore">{{ $t('studio.assets.loadMore') }}</ElButton>
    </div>

    <!-- 资产详情弹窗：关联任务的完整提示词 / 模型 / 参数 -->
    <GenDetailDialog v-model="detailVisible" :asset="detailAsset" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, UploadFile } from 'element-plus'
import {
  deleteAsset,
  getAsset,
  getSystemMeta,
  listAssets,
  StudioAsset,
  SystemMeta,
  uploadAsset
} from '@/api/studio'
import { ASSET_BADGE_CLASS, TASK_TYPE_KEY } from './utils'
import GenDetailDialog from './components/GenDetailDialog.vue'
import './style.scss'

defineOptions({ name: 'StudioAssets' })

const { t } = useI18n()

/** 类型筛选 tabs（computed 保证语言切换后文案更新） */
const typeTabs = computed<{ key: '' | 'generate' | 'matting' | 'upload'; label: string }[]>(() => [
  { key: '', label: t('studio.assets.all') },
  { key: 'generate', label: t('studio.common.taskType.generate') },
  { key: 'matting', label: t('studio.common.taskType.matting') },
  { key: 'upload', label: t('studio.common.taskType.upload') }
])

/** 类型 → 文案（未知类型回退显示原值） */
const typeText = (type: string) => {
  const key = TASK_TYPE_KEY[type]
  return key ? t(key) : type
}

const PAGE_SIZE = 24

const activeType = ref<'' | 'generate' | 'matting' | 'upload'>('')
const assets = ref<StudioAsset[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const uploading = ref(false)
const meta = ref<SystemMeta | null>(null)
const detailVisible = ref(false)
const detailAsset = ref<StudioAsset | null>(null)

/** 资产详情：重新拉取一次（后端会附带源任务 params/result） */
const showDetail = async (asset: StudioAsset) => {
  detailAsset.value = asset
  detailVisible.value = true
  try {
    const res = await getAsset(asset.id)
    if (res.data) detailAsset.value = res.data
  } catch {
    // 列表数据兜底
  }
}

const activeTypeText = computed(
  () => typeTabs.value.find((tab) => tab.key === activeType.value)?.label ?? t('studio.assets.all')
)

const load = async (append = false) => {
  loading.value = true
  try {
    const res = await listAssets({
      type: activeType.value || undefined,
      page: page.value,
      page_size: PAGE_SIZE
    })
    total.value = res.data?.total ?? 0
    const items = res.data?.items ?? []
    assets.value = append ? [...assets.value, ...items] : items
  } catch {
    ElMessage.error(t('studio.assets.loadFailed'))
  } finally {
    loading.value = false
  }
}

const switchType = (key: '' | 'generate' | 'matting' | 'upload') => {
  activeType.value = key
  page.value = 1
  load()
}

const loadMore = () => {
  page.value += 1
  load(true)
}

const remove = (asset: StudioAsset) => {
  ElMessageBox.confirm(t('studio.assets.deleteConfirm', { n: asset.id }), t('studio.assets.deleteTitle'), {
    type: 'warning',
    confirmButtonText: t('studio.common.actions.confirm'),
    cancelButtonText: t('studio.common.actions.cancel')
  })
    .then(async () => {
      await deleteAsset(asset.id)
      ElMessage.success(t('studio.assets.deleted'))
      load()
    })
    .catch(() => undefined)
}

/** 手工上传图片入库（type=upload） */
const onUpload = async (file: UploadFile) => {
  if (!file.raw) return
  uploading.value = true
  try {
    await uploadAsset(file.raw, t('studio.assets.manualUpload'))
    ElMessage.success(t('studio.assets.uploadSuccess'))
    page.value = 1
    activeType.value = 'upload'
    load()
  } catch {
    ElMessage.error(t('studio.assets.uploadFailed'))
  } finally {
    uploading.value = false
  }
}

const formatTime = (iso: string) => {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('zh-CN', { hour12: false })
}

onMounted(async () => {
  load()
  // 存储信息条：后端根路由元信息（P1 无 /api/system/info，仅展示名称与版本）
  try {
    const res = await getSystemMeta()
    meta.value = res.data
  } catch {
    // 元信息失败不阻塞列表
  }
})
</script>

<style lang="scss" scoped>
  .storage-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    margin-bottom: 14px;
    font-size: 12px;
    color: var(--art-gray-600);

    .divider {
      color: var(--art-border-dashed-color);
    }
  }

  .tabs-row {
    display: flex;
    gap: 6px;
    margin-bottom: 14px;
  }

  .tab-item {
    padding: 7px 16px;
    font-size: 13px;
    border-radius: 6px;
    cursor: pointer;
    color: var(--art-gray-600);

    &:hover {
      color: var(--art-primary);
    }

    &.on {
      background: rgba(37, 99, 235, 0.15);
      color: var(--art-primary);
      font-weight: 600;
    }
  }

  .asset-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 14px;
  }

  .asset-thumb {
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

  .asset-meta {
    margin-top: 8px;

    .asset-title {
      font-size: 12px;
      font-weight: 600;
      color: var(--art-text-gray-900);
    }

    .asset-sub {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 4px;

      .asset-badge {
        font-size: 10px;
      }

      .time {
        font-size: 10px;
        color: var(--art-gray-500);
      }
    }
  }

  .truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .load-more {
    display: flex;
    justify-content: center;
    margin-top: 18px;
  }
</style>

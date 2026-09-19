<!-- 资产库：类型筛选 + 卡片网格 + 删除/下载 + 存储概览 -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>资产库</h1>
        <p class="desc">生图 / 抠图 / 上传产物统一存储与管理</p>
      </div>
      <ElUpload :show-file-list="false" :auto-upload="false" accept="image/*" :on-change="onUpload">
        <ElButton type="primary" :loading="uploading">⬆ 上传图片</ElButton>
      </ElUpload>
    </div>

    <!-- 存储信息条 -->
    <div class="storage-bar studio-card" v-if="meta">
      <span>📦 {{ meta.name }} v{{ meta.version }}</span>
      <span class="divider">|</span>
      <span>资产总数 {{ total }}</span>
      <span class="divider">|</span>
      <span>当前筛选：{{ activeTypeText }}</span>
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
            <ElButton size="small" @click.stop="showDetail(asset)">详情</ElButton>
            <ElButton size="small" tag="a" :href="asset.url" target="_blank">⬇</ElButton>
            <ElButton size="small" type="danger" @click="remove(asset)">🗑</ElButton>
          </div>
        </div>
        <div class="asset-meta">
          <div class="asset-title">
            <span class="truncate">#{{ asset.id }} {{ asset.labels || asset.filename || '未命名' }}</span>
          </div>
          <div class="asset-sub">
            <i :class="ASSET_BADGE_CLASS[asset.type]">{{ TASK_TYPE_TEXT[asset.type] }}</i>
            <span class="time">{{ formatTime(asset.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="studio-empty"><span>暂无资产</span></div>

    <div v-if="total > assets.length" class="load-more">
      <ElButton :loading="loading" @click="loadMore">加载更多</ElButton>
    </div>

    <!-- 资产详情弹窗：关联任务的完整提示词 / 模型 / 参数 -->
    <GenDetailDialog v-model="detailVisible" :asset="detailAsset" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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
import { ASSET_BADGE_CLASS, TASK_TYPE_TEXT } from './utils'
import GenDetailDialog from './components/GenDetailDialog.vue'
import './style.scss'

defineOptions({ name: 'StudioAssets' })

const typeTabs = [
  { key: '', label: '全部' },
  { key: 'generate', label: '生图' },
  { key: 'matting', label: '抠图' },
  { key: 'upload', label: '上传' }
] as const

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

const activeTypeText = computed(() => typeTabs.find((t) => t.key === activeType.value)?.label ?? '全部')

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
    ElMessage.error('加载资产失败')
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
  ElMessageBox.confirm(`确认删除资产 #${asset.id}？磁盘文件将一并删除。`, '删除确认', { type: 'warning' })
    .then(async () => {
      await deleteAsset(asset.id)
      ElMessage.success('已删除')
      load()
    })
    .catch(() => undefined)
}

/** 手工上传图片入库（type=upload） */
const onUpload = async (file: UploadFile) => {
  if (!file.raw) return
  uploading.value = true
  try {
    await uploadAsset(file.raw, '手工上传')
    ElMessage.success('上传成功')
    page.value = 1
    activeType.value = 'upload'
    load()
  } catch {
    ElMessage.error('上传失败')
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

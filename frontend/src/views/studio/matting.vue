<!-- 抠图工具箱：上传/选资产 → 提交 → 前后对比（滑块） → 下载 -->
<template>
  <div class="studio-page">
    <div class="studio-header">
      <div>
        <h1>抠图工具箱</h1>
        <p class="desc">本地推理去背景 · 输出透明底 PNG · 模型来自「模型中心」</p>
      </div>
    </div>

    <div class="mat-layout">
      <!-- 左：源图与提交 -->
      <div class="mat-side">
        <div class="studio-card">
          <div class="card-title">抠图模型</div>
          <ElSelect v-model="model" style="width: 100%">
            <ElOption label="bria-rmbg（快速 · 通用）" value="bria-rmbg" />
            <ElOption label="birefnet（高精度 · 发丝边缘）" value="birefnet" />
          </ElSelect>

          <div class="card-title" style="margin-top: 16px">上传图片</div>
          <ElUpload
            drag
            :auto-upload="false"
            :show-file-list="false"
            accept="image/png,image/jpeg,image/webp"
            :on-change="onFileChange"
          >
            <div class="upload-inner">
              <div class="upload-icon">📁</div>
              <div class="upload-text">拖拽文件到此处，或 <em>点击选择</em></div>
              <div class="upload-sub">支持 PNG / JPG / WebP</div>
            </div>
          </ElUpload>

          <div v-if="sourcePreview" class="source-preview">
            <span class="source-name">{{ sourceName }}</span>
            <img :src="sourcePreview" alt="源图预览" />
          </div>

          <div class="card-title" style="margin-top: 16px">或选择已有资产</div>
          <div v-if="pickAssets.length" class="asset-pick">
            <div
              v-for="asset in pickAssets"
              :key="asset.id"
              class="pick-item"
              :class="{ on: selectedAssetId === asset.id }"
              @click="selectAsset(asset)"
            >
              <img :src="asset.thumb_url" loading="lazy" />
              <span class="pick-label">#{{ asset.id }}</span>
            </div>
          </div>
          <div v-else class="studio-empty"><span>资产库暂无可用图片</span></div>

          <ElButton
            type="primary"
            class="submit-btn"
            :loading="submitting || polling"
            :disabled="!canSubmit"
            @click="submit"
          >
            ✂️ 提交抠图任务
          </ElButton>
        </div>
      </div>

      <!-- 右：前后对比 -->
      <div class="studio-card mat-main">
        <div class="card-title">
          处理前后对比
          <span class="result-meta">拖动滑块查看抠图效果</span>
        </div>

        <div v-if="submitting || polling" class="studio-empty">
          <ElIcon class="is-loading" :size="24"><Loading /></ElIcon>
          <span>抠图任务执行中…</span>
        </div>

        <template v-else-if="sourceUrl && resultAsset">
          <CompareSlider :before="sourceUrl" :after="resultAsset.url" />
          <div class="compare-meta">
            <span>◀ 原图</span>
            <span>抠图结果（资产 #{{ resultAsset.id }}）▶</span>
          </div>
          <div class="compare-actions">
            <ElButton type="primary" tag="a" :href="resultAsset.url" target="_blank">⬇ 下载结果</ElButton>
            <ElButton @click="reset">再来一张</ElButton>
          </div>
        </template>

        <div v-else class="studio-empty"><span>上传图片或选择资产后提交，抠图结果将展示在这里</span></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, UploadFile } from 'element-plus'
import {
  getAsset,
  listAssets,
  StudioAsset,
  StudioTask,
  pollTask,
  submitMatting,
  taskAssetIds,
  uploadMatting
} from '@/api/studio'
import './style.scss'

defineOptions({ name: 'StudioMatting' })

/** 前后对比滑块：before 原图，after 抠图透明底（棋盘格衬底） */
const CompareSlider = defineComponent({
  name: 'CompareSlider',
  props: { before: { type: String, required: true }, after: { type: String, required: true } },
  setup(props) {
    const pos = ref(50)
    const onMove = (e: Event) => {
      pos.value = Number((e.target as HTMLInputElement).value)
    }
    return () =>
      h('div', { class: 'cmp-wrap studio-checker' }, [
        h('img', { class: 'cmp-after', src: props.after }),
        h('div', { class: 'cmp-clip', style: { width: `${pos.value}%` } }, [
          h('img', { class: 'cmp-before', src: props.before })
        ]),
        h('div', { class: 'cmp-handle', style: { left: `${pos.value}%` } }, '⇔'),
        h('input', {
          class: 'cmp-range',
          type: 'range',
          min: 0,
          max: 100,
          value: pos.value,
          onInput: onMove
        })
      ])
  }
})

const route = useRoute()

const model = ref('bria-rmbg')
const pickAssets = ref<StudioAsset[]>([])
const selectedAssetId = ref<number | null>(null)
const uploadFile = ref<File | null>(null)
const uploadPreview = ref('')
const sourceAsset = ref<StudioAsset | null>(null)
const resultAsset = ref<StudioAsset | null>(null)
const submitting = ref(false)
const polling = ref(false)

let pollTimer: ReturnType<typeof setTimeout> | null = null
let previewUrl: string | null = null

/** 展示用源图：上传预览优先，其次所选资产 */
const sourcePreview = computed(() => uploadPreview.value || sourceAsset.value?.url || '')
const sourceUrl = computed(() => (uploadFile.value ? uploadPreview.value : sourceAsset.value?.url || ''))
const sourceName = computed(() => uploadFile.value?.name || (sourceAsset.value ? `资产 #${sourceAsset.value.id}` : ''))
const canSubmit = computed(() => Boolean(uploadFile.value || selectedAssetId.value))

/** 从生图页跳转过来时预选资产 */
const preselectFromQuery = async () => {
  const q = Number(route.query.asset_id)
  if (!Number.isFinite(q) || q <= 0) return
  try {
    const res = await getAsset(q)
    if (res.data) selectAsset(res.data)
  } catch {
    // 预选失败不阻塞页面
  }
}

const loadPickAssets = async () => {
  try {
    // 优先给「生图产物」，其次任意资产
    const gen = await listAssets({ type: 'generate', page: 1, page_size: 8 })
    pickAssets.value = gen.data?.items ?? []
    if (!pickAssets.value.length) {
      const all = await listAssets({ page: 1, page_size: 8 })
      pickAssets.value = all.data?.items ?? []
    }
  } catch {
    // 资产列表拉取失败时展示空态
  }
}

const selectAsset = (asset: StudioAsset) => {
  selectedAssetId.value = asset.id
  sourceAsset.value = asset
  // 切换资产来源时清掉上传文件
  clearUpload()
}

const onFileChange = (file: UploadFile) => {
  const raw = file.raw
  if (!raw) return
  clearUpload()
  uploadFile.value = raw
  previewUrl = URL.createObjectURL(raw)
  uploadPreview.value = previewUrl
  selectedAssetId.value = null
}

const clearUpload = () => {
  uploadFile.value = null
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl)
    previewUrl = null
  }
  uploadPreview.value = ''
}

/** 提交：上传走 multipart 直传接口；选资产走 JSON 接口 */
const submit = async () => {
  if (!canSubmit.value) return
  submitting.value = true
  resultAsset.value = null
  try {
    let task: StudioTask
    if (uploadFile.value) {
      const res = await uploadMatting(uploadFile.value, model.value)
      task = res.data
    } else {
      const res = await submitMatting({ asset_id: selectedAssetId.value as number, model: model.value })
      task = res.data
    }
    await poll(task.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '提交抠图任务失败')
  } finally {
    submitting.value = false
  }
}

/** 轮询任务直至 done，取第一个产物资产做对比 */
const poll = async (taskId: number) => {
  polling.value = true
  try {
    const task = await pollTask(taskId, { timeoutMs: 180000 })
    const ids = taskAssetIds(task)
    if (!ids.length) {
      ElMessage.warning('任务完成但未产出资产')
      return
    }
    const res = await getAsset(ids[0])
    resultAsset.value = res.data
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '抠图任务失败')
  } finally {
    polling.value = false
  }
}

const reset = () => {
  resultAsset.value = null
  clearUpload()
  selectedAssetId.value = null
  sourceAsset.value = null
}

onMounted(() => {
  loadPickAssets()
  preselectFromQuery()
})

onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
  if (previewUrl) URL.revokeObjectURL(previewUrl)
})
</script>

<style lang="scss" scoped>
  .mat-layout {
    display: grid;
    grid-template-columns: minmax(300px, 4fr) minmax(0, 8fr);
    gap: 16px;
    align-items: start;
  }

  .upload-inner {
    padding: 14px 0;

    .upload-icon {
      font-size: 28px;
    }

    .upload-text {
      font-size: 13px;
      font-weight: 600;
      color: var(--art-text-gray-900);

      em {
        font-style: normal;
        color: #06b6d4;
      }
    }

    .upload-sub {
      margin-top: 4px;
      font-size: 11px;
      color: var(--art-gray-500);
    }
  }

  .source-preview {
    margin-top: 12px;

    .source-name {
      display: block;
      font-size: 11px;
      color: var(--art-gray-500);
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    img {
      width: 100%;
      max-height: 180px;
      object-fit: contain;
      border-radius: 6px;
      background: var(--art-gray-200);
    }
  }

  .asset-pick {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 14px;
    max-height: 180px;
    overflow-y: auto;
  }

  .pick-item {
    position: relative;
    aspect-ratio: 1;
    border-radius: 6px;
    overflow: hidden;
    border: 2px solid transparent;
    cursor: pointer;
    background: var(--art-gray-200);

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .pick-label {
      position: absolute;
      left: 0;
      bottom: 0;
      right: 0;
      font-size: 10px;
      text-align: center;
      color: #fff;
      background: linear-gradient(transparent, rgba(2, 6, 23, 0.85));
    }

    &.on {
      border-color: var(--art-primary);
    }
  }

  .submit-btn {
    width: 100%;
    height: 42px;
    font-size: 14px;
    margin-top: 6px;
  }

  .result-meta {
    font-weight: 400;
    font-size: 11px;
    color: var(--art-gray-500);
    margin-left: 8px;
  }

  .compare-meta {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--art-gray-500);
    margin-top: 6px;
  }

  .compare-actions {
    margin-top: 14px;
    display: flex;
    gap: 10px;
  }

  :deep(.cmp-wrap) {
    position: relative;
    width: 100%;
    aspect-ratio: 4 / 3;
    border-radius: 6px;
    overflow: hidden;
    user-select: none;

    .cmp-after,
    .cmp-before {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }

    .cmp-clip {
      position: absolute;
      inset: 0 auto 0 0;
      overflow: hidden;

      .cmp-before {
        width: 100%;
        height: 100%;
      }
    }

    .cmp-handle {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 2px;
      background: #06b6d4;
      transform: translateX(-1px);

      &::after {
        content: '⇔';
        position: absolute;
        top: 50%;
        left: -14px;
        width: 30px;
        height: 30px;
        line-height: 30px;
        text-align: center;
        background: #06b6d4;
        color: #04222b;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 700;
        transform: translateY(-50%);
      }
    }

    .cmp-range {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      opacity: 0;
      cursor: ew-resize;
      margin: 0;
    }
  }
</style>

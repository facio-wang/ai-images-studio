<!-- 生成详情弹窗（移植自 webUI-v1.0 生成参数折叠条）：完整提示词 / 模型 / 采样参数 / 产物图 -->
<template>
  <ElDialog v-model="visible" title="生成详情" width="560px" destroy-on-close>
    <template v-if="detail">
      <!-- 产物预览 -->
      <div v-if="assetUrls.length" class="detail-preview" :class="{ checker: assetType === 'matting' }">
        <img :src="assetUrls[0]" />
      </div>

      <ElAlert
        v-if="detail.error"
        type="error"
        :title="`失败原因：${briefError}`"
        :closable="false"
        style="margin-bottom: 12px"
      />

      <div class="kv-list">
        <div class="kv">
          <span class="k">提示词</span>
          <span class="v pre">{{ genParams.prompt || (props.asset as any)?.labels || '—' }}</span>
        </div>
        <div v-if="enhancedPrompt && enhancedPrompt !== genParams.prompt" class="kv">
          <span class="k">实际发送提示词</span>
          <span class="v pre">{{ enhancedPrompt }}</span>
        </div>
        <div v-if="negative" class="kv">
          <span class="k">反向提示词</span>
          <span class="v pre">{{ negative }}</span>
        </div>
        <div v-if="modelText" class="kv">
          <span class="k">生图模型</span>
          <span class="v">{{ modelText }}</span>
        </div>
        <div v-if="genParams.width" class="kv">
          <span class="k">尺寸</span>
          <span class="v">{{ genParams.width }} × {{ genParams.height }} · {{ genParams.count || 1 }} 张</span>
        </div>
        <div v-if="genParams.steps" class="kv">
          <span class="k">采样</span>
          <span class="v">{{ genParams.steps }} 步 · CFG {{ genParams.cfg }}</span>
        </div>
        <div v-if="seedText" class="kv">
          <span class="k">Seed</span>
          <span class="v accent">{{ seedText }}</span>
        </div>
        <div v-if="detail.type" class="kv">
          <span class="k">任务类型</span>
          <span class="v">{{ TASK_TYPE_TEXT[detail.type] || detail.type }}</span>
        </div>
        <div v-if="detail.created_at" class="kv">
          <span class="k">创建时间</span>
          <span class="v">{{ formatTime(detail.created_at) }}</span>
        </div>
        <div v-if="assetIdText" class="kv">
          <span class="k">产物资产</span>
          <span class="v">{{ assetIdText }}</span>
        </div>
      </div>

      <div class="detail-ops">
        <ElButton v-if="assetUrls.length" tag="a" :href="assetUrls[0]" target="_blank">⬇ 查看原图</ElButton>
        <ElButton
          v-if="detail.status === 'failed' || detail.error"
          type="warning"
          plain
          @click="$emit('retry')"
        >
          ⟳ 重试任务
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StudioAsset, StudioTask } from '@/api/studio'
import { TASK_TYPE_TEXT } from '../utils'

const props = defineProps<{ asset?: StudioAsset | null; task?: StudioTask | null }>()
defineEmits<{ (e: 'retry'): void }>()

const visible = defineModel<boolean>({ default: false })

const detail = computed<StudioTask | null>(() => {
  if (props.task) return props.task
  return props.asset?.task ?? null
})

const assetType = computed(() => props.asset?.type ?? (props.task?.type as StudioAsset['type']) ?? 'generate')

const genParams = computed<Record<string, any>>(() => {
  const p = detail.value?.params
  if (typeof p === 'string') {
    try {
      return JSON.parse(p)
    } catch {
      return {}
    }
  }
  return p ?? {}
})

const genResult = computed<Record<string, any>>(() => {
  const r = detail.value?.result
  if (typeof r === 'string') {
    try {
      return JSON.parse(r)
    } catch {
      return {}
    }
  }
  return r ?? {}
})

const enhancedPrompt = computed(() => String(genResult.value.enhanced_prompt ?? ''))
const negative = computed(() => String(genParams.value.negative ?? ''))
const modelText = computed(() => {
  const model = genResult.value.model ?? genParams.value.checkpoint
  if (!model) return ''
  const type = genResult.value.model_type
  return type === 'z_image' ? `${model}（Z-Image 原生中文）` : String(model)
})
const seedText = computed(() => {
  const s = genParams.value.seed
  const seed = genResult.value.params_snapshot?.seed ?? s
  return seed !== undefined && seed !== null ? String(seed) : ''
})

const assetUrls = computed<string[]>(() => {
  if (props.asset?.url) return [props.asset.url]
  return []
})

const assetIdText = computed(() => {
  const ids = genResult.value.asset_ids
  return Array.isArray(ids) && ids.length ? ids.map((id) => `#${id}`).join('、') : ''
})

const briefError = computed(() =>
  String(detail.value?.error ?? '')
    .split('\n')[0]
    .slice(0, 200)
)

const formatTime = (iso: string) => {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('zh-CN', { hour12: false })
}
</script>

<style lang="scss" scoped>
  .detail-preview {
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 14px;
    max-height: 320px;
    display: flex;
    justify-content: center;
    background: var(--art-gray-200);

    img {
      max-width: 100%;
      max-height: 320px;
      object-fit: contain;
    }
  }

  .kv-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .kv {
    display: flex;
    gap: 12px;
    font-size: 12.5px;
    line-height: 1.6;

    .k {
      width: 96px;
      flex-shrink: 0;
      color: var(--art-gray-500);
    }

    .v {
      flex: 1;
      min-width: 0;
      color: var(--art-text-gray-900);
      word-break: break-all;

      &.pre {
        white-space: pre-wrap;
      }

      &.accent {
        color: var(--art-primary);
        font-weight: 600;
      }
    }
  }

  .detail-ops {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
</style>

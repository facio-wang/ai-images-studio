<!-- 首次访问引导向导：4 步走完基础配置，localStorage 记忆已完成状态 -->
<template>
  <ElDialog
    v-model="visible"
    :title="$t('studio.onboarding.title')"
    width="560px"
    :close-on-click-modal="false"
    @closed="onClosed"
  >
    <!-- 步骤条 -->
    <ElSteps :active="step" simple finish-status="success" class="guide-steps">
      <ElStep :title="$t('studio.onboarding.steps.welcome')" />
      <ElStep :title="$t('studio.onboarding.steps.generate')" />
      <ElStep :title="$t('studio.onboarding.steps.translate')" />
      <ElStep :title="$t('studio.onboarding.steps.done')" />
    </ElSteps>

    <div class="guide-body">
      <!-- Step 1 欢迎简介 -->
      <div v-if="step === 0" class="guide-pane">
        <i18n-t keypath="studio.onboarding.s1.lead" tag="p" class="guide-lead" scope="global">
          <template #local><b>{{ $t('studio.onboarding.terms.localRun') }}</b></template>
        </i18n-t>
        <ul class="guide-list">
          <i18n-t keypath="studio.onboarding.s1.gen" tag="li" scope="global">
            <template #term><b>{{ $t('studio.common.taskType.generate') }}</b></template>
          </i18n-t>
          <i18n-t keypath="studio.onboarding.s1.translate" tag="li" scope="global">
            <template #term><b>{{ $t('studio.onboarding.terms.translate') }}</b></template>
          </i18n-t>
          <i18n-t keypath="studio.onboarding.s1.matting" tag="li" scope="global">
            <template #term><b>{{ $t('studio.common.taskType.matting') }}</b></template>
          </i18n-t>
        </ul>
        <p class="guide-note">{{ $t('studio.onboarding.s1.note') }}</p>
      </div>

      <!-- Step 2 生图配置 -->
      <div v-else-if="step === 1" class="guide-pane">
        <i18n-t keypath="studio.onboarding.s2.lead" tag="p" class="guide-lead" scope="global">
          <template #comfy><b>ComfyUI</b></template>
        </i18n-t>
        <ElInput v-model="comfyAddr" :placeholder="$t('studio.onboarding.s2.addrPlaceholder')">
          <template #prepend>{{ $t('studio.onboarding.s2.addrLabel') }}</template>
        </ElInput>
        <div class="guide-actions-row">
          <ElButton type="primary" :loading="syncing" @click="syncCheckpoints">{{ $t('studio.onboarding.s2.syncBtn') }}</ElButton>
          <span class="guide-hint">{{ $t('studio.onboarding.s2.syncHint') }}</span>
        </div>
        <p class="guide-note">{{ $t('studio.onboarding.s2.note') }}</p>
      </div>

      <!-- Step 3 翻译配置 -->
      <div v-else-if="step === 2" class="guide-pane">
        <i18n-t keypath="studio.onboarding.s3.lead" tag="p" class="guide-lead" scope="global">
          <template #api><b>{{ $t('studio.onboarding.terms.openaiCompat') }}</b></template>
        </i18n-t>
        <ul class="guide-list">
          <i18n-t keypath="studio.onboarding.s3.baseUrl" tag="li" scope="global">
            <template #field><b>base_url</b></template>
            <template #url><code>https://api.openai.com/v1</code></template>
          </i18n-t>
          <i18n-t keypath="studio.onboarding.s3.apiKeyTip" tag="li" scope="global">
            <template #field><b>api_key</b></template>
            <template #keySample><code>sk-...</code></template>
          </i18n-t>
          <i18n-t keypath="studio.onboarding.s3.modelId" tag="li" scope="global">
            <template #field><b>model_id</b></template>
            <template #m1><code>gpt-4o-mini</code></template>
            <template #m2><code>deepseek-chat</code></template>
          </i18n-t>
        </ul>
        <div class="guide-actions-row">
          <ElButton type="primary" @click="$router.push('/manage/models'); visible = false">{{ $t('studio.onboarding.s3.addModelBtn') }}</ElButton>
        </div>
        <p class="guide-note">{{ $t('studio.onboarding.s3.note') }}</p>
      </div>

      <!-- Step 4 完成 -->
      <div v-else class="guide-pane guide-done">
        <div class="done-icon">🚀</div>
        <p class="guide-lead">{{ $t('studio.onboarding.s4.lead') }}</p>
        <p class="guide-note">{{ $t('studio.onboarding.s4.note') }}</p>
      </div>
    </div>

    <template #footer>
      <ElButton v-if="step < 3" link @click="finish">{{ $t('studio.onboarding.skip') }}</ElButton>
      <ElButton v-if="step > 0 && step < 3" @click="step--">{{ $t('studio.onboarding.prev') }}</ElButton>
      <ElButton v-if="step < 3" type="primary" @click="step++">{{ step === 2 ? $t('studio.onboarding.next') : $t('studio.onboarding.next') }}</ElButton>
      <ElButton v-else type="primary" @click="goGenerate">{{ $t('studio.onboarding.startGenerate') }}</ElButton>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { syncCheckpointsApi } from '@/api/studio'

defineOptions({ name: 'OnboardingGuide' })

const emit = defineEmits<{ (e: 'finished'): void }>()
const router = useRouter()
const { t } = useI18n()

/** localStorage 记忆键：完成/跳过过引导就不再自动弹出 */
const DONE_KEY = 'studio_onboarding_done'

const visible = ref(false)
const step = ref(0)
const comfyAddr = ref('127.0.0.1:8188')
const syncing = ref(false)

const finish = () => {
  localStorage.setItem(DONE_KEY, '1')
  visible.value = false
}

const onClosed = () => {
  // 关闭即视为完成，避免下次重复打扰
  localStorage.setItem(DONE_KEY, '1')
  emit('finished')
}

const goGenerate = () => {
  finish()
  router.push('/creation/generate')
}

const syncCheckpoints = async () => {
  syncing.value = true
  try {
    const res = await syncCheckpointsApi()
    ElMessage.success(t('studio.onboarding.syncDone', { n: res.data?.added ?? 0 }))
  } catch {
    ElMessage.warning(t('studio.onboarding.syncFail'))
  } finally {
    syncing.value = false
  }
}

/** 首次访问（无记忆标记）自动弹出；供 home 页「重新查看」调用 */
const open = () => {
  step.value = 0
  visible.value = true
}
defineExpose({ open })

// 首次进入自动弹出（已完成/跳过过则不弹）
if (!localStorage.getItem(DONE_KEY)) {
  visible.value = true
}
</script>

<style lang="scss" scoped>
  .guide-steps {
    margin-bottom: 16px;
  }

  .guide-body {
    min-height: 180px;
  }

  .guide-pane {
    font-size: 13px;
    line-height: 1.8;
    color: var(--art-gray-600);

    code {
      padding: 1px 5px;
      font-size: 11px;
      font-family: monospace;
      background: rgba(37, 99, 235, 0.08);
      border-radius: 4px;
    }
  }

  .guide-lead {
    margin-bottom: 10px;
    font-size: 13.5px;
    color: var(--art-text-gray-900);
  }

  .guide-list {
    padding-left: 18px;
    margin-bottom: 10px;

    li {
      margin-bottom: 4px;
    }
  }

  .guide-note {
    font-size: 11.5px;
    color: var(--art-gray-500);
  }

  .guide-actions-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 12px 0;
  }

  .guide-hint {
    font-size: 11.5px;
    color: var(--art-gray-500);
  }

  .guide-done {
    text-align: center;

    .done-icon {
      font-size: 40px;
      margin-bottom: 8px;
    }
  }
</style>

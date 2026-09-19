<!-- 首次访问引导向导：4 步走完基础配置，localStorage 记忆已完成状态 -->
<template>
  <ElDialog
    v-model="visible"
    title="🎉 欢迎使用 AI Images Studio"
    width="560px"
    :close-on-click-modal="false"
    @closed="onClosed"
  >
    <!-- 步骤条 -->
    <ElSteps :active="step" simple finish-status="success" class="guide-steps">
      <ElStep title="欢迎" />
      <ElStep title="生图配置" />
      <ElStep title="翻译配置" />
      <ElStep title="完成" />
    </ElSteps>

    <div class="guide-body">
      <!-- Step 1 欢迎简介 -->
      <div v-if="step === 0" class="guide-pane">
        <p class="guide-lead">这是一个<b>本地运行</b>的 AI 创作平台，所有模型、图片和数据库都保存在你自己的电脑上，不会上传到任何云端。</p>
        <ul class="guide-list">
          <li>🎨 <b>生图</b>：连接本机 ComfyUI，输入提示词生成图片</li>
          <li>🌐 <b>翻译</b>：把中文提示词翻译成英文（需要一个 OpenAI 兼容接口）</li>
          <li>✂️ <b>抠图</b>：一键去除图片背景</li>
        </ul>
        <p class="guide-note">下面用 2 分钟完成初始配置，随时可以跳过。</p>
      </div>

      <!-- Step 2 生图配置 -->
      <div v-else-if="step === 1" class="guide-pane">
        <p class="guide-lead">生图依赖本机的 <b>ComfyUI</b> 服务。请确认 ComfyUI 已启动，并核对服务地址：</p>
        <ElInput v-model="comfyAddr" placeholder="127.0.0.1:8188 或 192.168.31.57:8188">
          <template #prepend>ComfyUI 地址</template>
        </ElInput>
        <div class="guide-actions-row">
          <ElButton type="primary" :loading="syncing" @click="syncCheckpoints">一键同步底模</ElButton>
          <span class="guide-hint">把 ComfyUI 里已安装的底模列表同步到模型中心</span>
        </div>
        <p class="guide-note">如果同步失败，多半是 ComfyUI 没启动或地址不对，可先跳过稍后在系统设置里修改。</p>
      </div>

      <!-- Step 3 翻译配置 -->
      <div v-else-if="step === 2" class="guide-pane">
        <p class="guide-lead">翻译功能需要一个 <b>OpenAI 兼容接口</b>。到「模型中心 → 翻译」新增一个翻译模型，需要填 3 个字段：</p>
        <ul class="guide-list">
          <li><b>base_url</b>：API 服务地址，如 <code>https://api.openai.com/v1</code>。各家服务商都会提供，自建中转站则填中转站地址</li>
          <li><b>api_key</b>：密钥，在服务商控制台申请，形如 <code>sk-...</code>，注意保密</li>
          <li><b>model_id</b>：要调用的模型名，如 <code>gpt-4o-mini</code>、<code>deepseek-chat</code></li>
        </ul>
        <div class="guide-actions-row">
          <ElButton type="primary" @click="$router.push('/manage/models'); visible = false">去模型中心添加</ElButton>
        </div>
        <p class="guide-note">没有海外卡？可以用硅基流动、DeepSeek 等国内服务商，或自建中转站。详见帮助页。</p>
      </div>

      <!-- Step 4 完成 -->
      <div v-else class="guide-pane guide-done">
        <div class="done-icon">🚀</div>
        <p class="guide-lead">配置完成！随时可以回到工作台查看快捷入口。</p>
        <p class="guide-note">遇到问题？顶部导航的「帮助中心」有完整教程和常见问题解答。</p>
      </div>
    </div>

    <template #footer>
      <ElButton v-if="step < 3" link @click="finish">跳过引导</ElButton>
      <ElButton v-if="step > 0 && step < 3" @click="step--">上一步</ElButton>
      <ElButton v-if="step < 3" type="primary" @click="step++">{{ step === 2 ? '下一步' : '下一步' }}</ElButton>
      <ElButton v-else type="primary" @click="goGenerate">开始生图 →</ElButton>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { syncCheckpointsApi } from '@/api/studio'

defineOptions({ name: 'OnboardingGuide' })

const emit = defineEmits<{ (e: 'finished'): void }>()
const router = useRouter()

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
    ElMessage.success(`同步完成：新增 ${res.data?.added ?? 0} 个底模`)
  } catch {
    ElMessage.warning('同步失败，请确认 ComfyUI 已启动、地址正确')
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

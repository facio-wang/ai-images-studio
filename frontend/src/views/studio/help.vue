<!-- 帮助中心：左侧锚点导航 + 右侧文档（快速上手 / 模型配置 / FAQ） -->
<template>
  <div class="studio-page help-page">
    <div class="studio-header">
      <div>
        <h1>{{ $t('studio.help.title') }}</h1>
        <p class="desc">{{ $t('studio.help.desc') }}</p>
      </div>
    </div>

    <div class="help-layout">
      <!-- 左侧锚点导航 -->
      <div class="studio-card help-nav">
        <div
          v-for="sec in sections"
          :key="sec.id"
          class="nav-item"
          :class="{ on: activeAnchor === sec.id }"
          @click="scrollTo(sec.id)"
        >
          {{ sec.label }}
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="help-content">
        <!-- 快速上手 -->
        <div id="sec-quickstart" class="studio-card help-section">
          <h2>{{ $t('studio.help.quickstart.title') }}</h2>
          <div class="step-block">
            <div class="step-no">1</div>
            <div>
              <h3>{{ $t('studio.help.quickstart.step1Title') }}</h3>
              <p>{{ $t('studio.help.quickstart.step1Body1') }}<code>127.0.0.1:8188</code>{{ $t('studio.help.quickstart.step1Body2') }}</p>
            </div>
          </div>
          <div class="step-block">
            <div class="step-no">2</div>
            <div>
              <h3>{{ $t('studio.help.quickstart.step2Title') }}</h3>
              <p>{{ $t('studio.help.quickstart.step2Body') }}</p>
            </div>
          </div>
          <div class="step-block">
            <div class="step-no">3</div>
            <div>
              <h3>{{ $t('studio.help.quickstart.step3Title') }}</h3>
              <p>{{ $t('studio.help.quickstart.step3Body') }}</p>
            </div>
          </div>
        </div>

        <!-- 模型配置详解 -->
        <div id="sec-models" class="studio-card help-section">
          <h2>{{ $t('studio.help.models.title') }}</h2>
          <p class="section-lead">{{ $t('studio.help.models.lead') }}</p>

          <h3>{{ $t('studio.help.models.checkpointTitle') }}</h3>
          <p>{{ $t('studio.help.models.checkpointBody') }}</p>

          <h3>{{ $t('studio.help.models.loraTitle') }}</h3>
          <p>{{ $t('studio.help.models.loraBody1') }}<code>{"trigger": "sks style"}</code>{{ $t('studio.help.models.loraBody2') }}</p>

          <h3>{{ $t('studio.help.models.mattingTitle') }}</h3>
          <p>{{ $t('studio.help.models.mattingBody') }}</p>

          <h3>{{ $t('studio.help.models.translateTitle') }}</h3>
          <p>{{ $t('studio.help.models.translateBody1') }}<b>{{ $t('studio.help.models.translateBold') }}</b>{{ $t('studio.help.models.translateBody2') }}</p>
          <div class="field-table">
            <div class="field-row head">
              <span>{{ $t('studio.help.models.fieldTable.field') }}</span>
              <span>{{ $t('studio.help.models.fieldTable.what') }}</span>
              <span>{{ $t('studio.help.models.fieldTable.where') }}</span>
            </div>
            <div class="field-row">
              <span><code>base_url</code></span>
              <span>{{ $t('studio.help.models.fieldTable.baseUrlWhat') }}</span>
              <span>{{ $t('studio.help.models.fieldTable.baseUrlWhere1') }}<code>/v1</code>{{ $t('studio.help.models.fieldTable.baseUrlWhere2') }}</span>
            </div>
            <div class="field-row">
              <span><code>api_key</code></span>
              <span>{{ $t('studio.help.models.fieldTable.apiKeyWhat') }}</span>
              <span>{{ $t('studio.help.models.fieldTable.apiKeyWhere') }}</span>
            </div>
            <div class="field-row">
              <span><code>model_id</code></span>
              <span>{{ $t('studio.help.models.fieldTable.modelIdWhat') }}</span>
              <span>{{ $t('studio.help.models.fieldTable.modelIdWhere') }}</span>
            </div>
          </div>

          <h3>{{ $t('studio.help.models.providers.title') }}</h3>
          <div class="field-table">
            <div class="field-row head">
              <span>{{ $t('studio.help.models.providers.headProvider') }}</span>
              <span>base_url</span>
              <span>{{ $t('studio.help.models.providers.headModelId') }}</span>
            </div>
            <div class="field-row">
              <span>{{ $t('studio.help.models.providers.openai') }}</span>
              <span><code>https://api.openai.com/v1</code></span>
              <span><code>gpt-4o-mini</code></span>
            </div>
            <div class="field-row">
              <span>{{ $t('studio.help.models.providers.siliconflow') }}</span>
              <span><code>https://api.siliconflow.cn/v1</code></span>
              <span><code>Qwen/Qwen2.5-7B-Instruct</code></span>
            </div>
            <div class="field-row">
              <span>DeepSeek</span>
              <span><code>https://api.deepseek.com/v1</code></span>
              <span><code>deepseek-chat</code></span>
            </div>
            <div class="field-row">
              <span>{{ $t('studio.help.models.providers.relay') }}</span>
              <span><code>{{ $t('studio.help.models.providers.relayUrl') }}</code></span>
              <span>{{ $t('studio.help.models.providers.relayModels') }}</span>
            </div>
          </div>
          <p class="section-note">{{ $t('studio.help.models.note') }}</p>
        </div>

        <!-- 常见问题 -->
        <div id="sec-faq" class="studio-card help-section">
          <h2>{{ $t('studio.help.faq.title') }}</h2>

          <h3>{{ $t('studio.help.faq.q1') }}</h3>
          <p>{{ $t('studio.help.faq.a1p1') }}<code>192.168.31.57:8188</code>{{ $t('studio.help.faq.a1p2') }}<code>--listen</code>{{ $t('studio.help.faq.a1p3') }}</p>

          <h3>{{ $t('studio.help.faq.q2') }}</h3>
          <p>{{ $t('studio.help.faq.a2') }}</p>

          <h3>{{ $t('studio.help.faq.q3') }}</h3>
          <p>{{ $t('studio.help.faq.a3p1') }}<code>data/u2net/</code>{{ $t('studio.help.faq.a3p2') }}</p>

          <h3>{{ $t('studio.help.faq.q4') }}</h3>
          <p>{{ $t('studio.help.faq.a4') }}</p>

          <h3>{{ $t('studio.help.faq.q5') }}</h3>
          <p>{{ $t('studio.help.faq.a5p1') }}<code>data/studio.db</code>{{ $t('studio.help.faq.a5p2') }}<code>data/assets/</code>{{ $t('studio.help.faq.a5p3') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import './style.scss'

defineOptions({ name: 'StudioHelp' })

const { t } = useI18n()

/** 左侧锚点目录（computed 保证语言切换后文案更新） */
const sections = computed(() => [
  { id: 'sec-quickstart', label: t('studio.help.nav.quickstart') },
  { id: 'sec-models', label: t('studio.help.nav.models') },
  { id: 'sec-faq', label: t('studio.help.nav.faq') }
])

const activeAnchor = ref('sec-quickstart')

const scrollTo = (id: string) => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

/** 滚动监听：高亮当前所在章节 */
const onScroll = () => {
  for (const sec of sections.value) {
    const el = document.getElementById(sec.id)
    if (el && el.getBoundingClientRect().top < 120) {
      activeAnchor.value = sec.id
    }
  }
}

onMounted(() => window.addEventListener('scroll', onScroll, true))
onBeforeUnmount(() => window.removeEventListener('scroll', onScroll, true))
</script>

<style lang="scss" scoped>
  .help-layout {
    display: grid;
    grid-template-columns: 200px minmax(0, 1fr);
    gap: 16px;
    align-items: start;
  }

  .help-nav {
    position: sticky;
    top: 80px;
    padding: 10px;

    .nav-item {
      padding: 9px 12px;
      font-size: 13px;
      border-radius: 6px;
      cursor: pointer;
      color: var(--art-gray-600);

      &:hover {
        color: var(--art-primary);
      }

      &.on {
        background: rgba(37, 99, 235, 0.12);
        color: var(--art-primary);
        font-weight: 600;
      }
    }
  }

  .help-section {
    margin-bottom: 16px;

    h2 {
      margin-bottom: 8px;
      font-size: 17px;
    }

    h3 {
      margin: 16px 0 6px;
      font-size: 14px;
    }

    p {
      margin-bottom: 8px;
      font-size: 13px;
      line-height: 1.8;
      color: var(--art-gray-600);
    }

    code {
      padding: 1px 5px;
      font-size: 11.5px;
      font-family: monospace;
      color: var(--art-primary);
      background: rgba(37, 99, 235, 0.08);
      border-radius: 4px;
      word-break: break-all;
    }
  }

  .section-lead {
    margin-bottom: 12px;
  }

  .section-note {
    font-size: 11.5px !important;
    color: var(--art-gray-500) !important;
  }

  /* 快速上手的分步块 */
  .step-block {
    display: flex;
    gap: 12px;
    padding: 12px 0;

    & + .step-block {
      border-top: 1px dashed var(--art-border-dashed-color);
    }

    .step-no {
      flex-shrink: 0;
      width: 26px;
      height: 26px;
      font-size: 13px;
      font-weight: 700;
      line-height: 26px;
      text-align: center;
      color: #fff;
      background: var(--art-primary);
      border-radius: 50%;
    }

    h3 {
      margin: 0 0 4px;
    }
  }

  /* 字段/服务商对照表 */
  .field-table {
    margin: 10px 0 14px;
    border: 1px solid var(--art-border-dashed-color);
    border-radius: 6px;
    overflow: hidden;

    .field-row {
      display: grid;
      grid-template-columns: 130px minmax(0, 1fr) minmax(0, 1.4fr);
      gap: 10px;
      padding: 8px 12px;
      font-size: 12px;
      line-height: 1.7;
      color: var(--art-gray-600);

      & + .field-row {
        border-top: 1px solid var(--art-border-dashed-color);
      }

      &.head {
        font-weight: 600;
        color: var(--art-text-gray-900);
        background: rgba(37, 99, 235, 0.06);
      }
    }
  }
</style>

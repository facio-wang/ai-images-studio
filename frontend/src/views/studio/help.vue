<!-- 帮助中心：左侧锚点导航 + 右侧文档（快速上手 / 模型配置 / FAQ） -->
<template>
  <div class="studio-page help-page">
    <div class="studio-header">
      <div>
        <h1>帮助中心</h1>
        <p class="desc">从零开始的配置指南与常见问题解答</p>
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
          <h2>🚀 快速上手：三步开始生图</h2>
          <div class="step-block">
            <div class="step-no">1</div>
            <div>
              <h3>启动 ComfyUI 并同步底模</h3>
              <p>确保本机 ComfyUI 已运行（默认 <code>127.0.0.1:8188</code>）。到「模型中心」点「同步 ComfyUI 底模」，已安装的底模会自动出现在底模分区。</p>
            </div>
          </div>
          <div class="step-block">
            <div class="step-no">2</div>
            <div>
              <h3>选一个默认底模</h3>
              <p>在底模分区点击「设默认」，生图页会自动使用默认底模；也可以在生图页临时切换。</p>
            </div>
          </div>
          <div class="step-block">
            <div class="step-no">3</div>
            <div>
              <h3>输入提示词开始生成</h3>
              <p>到「生图」页输入描述（支持先翻译成英文），设置尺寸与步数后提交。完成后图片自动进入资产库。</p>
            </div>
          </div>
        </div>

        <!-- 模型配置详解 -->
        <div id="sec-models" class="studio-card help-section">
          <h2>🧠 模型配置详解</h2>
          <p class="section-lead">平台共有四类模型，全部在「模型中心」统一管理。前三类本机即可配置，翻译模型需要外部 API。</p>

          <h3>底模（checkpoint）</h3>
          <p>文生图的主模型。推荐直接用「同步 ComfyUI 底模」一键导入，无需手填。也可以手动新增，名称需与 ComfyUI models/checkpoints 目录下的文件名一致。</p>

          <h3>LoRA</h3>
          <p>风格微调模型。手动新增，名称与 ComfyUI models/loras 目录下的文件名一致，附加信息可标注触发词，如 <code>{"trigger": "sks style"}</code>。</p>

          <h3>抠图（matting）</h3>
          <p>背景移除模型（如 bria-rmbg、birefnet）。首次使用时会自动下载到本机 data 目录，无需 API。</p>

          <h3>翻译（translate）— 重点</h3>
          <p>翻译模型通过 <b>OpenAI 兼容接口</b>调用大模型完成中译英，新增时需要填 3 个字段：</p>
          <div class="field-table">
            <div class="field-row head"><span>字段</span><span>是什么</span><span>从哪获取</span></div>
            <div class="field-row">
              <span><code>base_url</code></span>
              <span>API 服务根地址</span>
              <span>服务商文档提供，通常以 <code>/v1</code> 结尾</span>
            </div>
            <div class="field-row">
              <span><code>api_key</code></span>
              <span>访问密钥，形如 sk-...</span>
              <span>服务商控制台「API Keys」页面创建</span>
            </div>
            <div class="field-row">
              <span><code>model_id</code></span>
              <span>要调用的具体模型名</span>
              <span>服务商模型列表页，如 gpt-4o-mini</span>
            </div>
          </div>

          <h3>常见服务商示例</h3>
          <div class="field-table">
            <div class="field-row head"><span>服务商</span><span>base_url</span><span>model_id 示例</span></div>
            <div class="field-row">
              <span>OpenAI 官方</span>
              <span><code>https://api.openai.com/v1</code></span>
              <span><code>gpt-4o-mini</code></span>
            </div>
            <div class="field-row">
              <span>硅基流动</span>
              <span><code>https://api.siliconflow.cn/v1</code></span>
              <span><code>Qwen/Qwen2.5-7B-Instruct</code></span>
            </div>
            <div class="field-row">
              <span>DeepSeek</span>
              <span><code>https://api.deepseek.com/v1</code></span>
              <span><code>deepseek-chat</code></span>
            </div>
            <div class="field-row">
              <span>自建中转站</span>
              <span><code>https://你的中转域名/v1</code></span>
              <span>看中转站支持的模型列表</span>
            </div>
          </div>
          <p class="section-note">任何宣称「OpenAI 兼容」的服务都可以用。密钥只保存在本机数据库中。</p>
        </div>

        <!-- 常见问题 -->
        <div id="sec-faq" class="studio-card help-section">
          <h2>❓ 常见问题 FAQ</h2>

          <h3>ComfyUI 连不上怎么办？</h3>
          <p>依次检查：① ComfyUI 是否已启动（浏览器能打开 http://127.0.0.1:8188 即正常）；② 地址端口是否正确，ComfyUI 在其他机器时用那台机器的 IP（如 <code>192.168.31.57:8188</code>），且启动时需要加 <code>--listen</code>；③ 防火墙是否放行 8188 端口。</p>

          <h3>翻译报 401 是什么意思？</h3>
          <p>401 = 密钥无效。检查：① api_key 是否复制完整（没有多余空格）；② 密钥是否已过期或被禁用；③ 账户是否有余额。到「模型中心 → 翻译 → 编辑」更新密钥即可。</p>

          <h3>抠图模型下载失败怎么办？</h3>
          <p>抠图模型首次使用时从 GitHub/HuggingFace 下载，网络不通会失败。可手动下载模型文件（如 u2netp.onnx）放到本机 <code>data/u2net/</code> 目录后重试。</p>

          <h3>生图任务一直排队？</h3>
          <p>任务由本机 worker 逐个执行，ComfyUI 正在出图时新任务会排队。若长时间不动，到「任务中心」查看任务错误信息，或检查 ComfyUI 是否卡死。</p>

          <h3>数据都存在哪里？</h3>
          <p>全部在本机：<code>data/studio.db</code> 是数据库（模型配置、任务记录），<code>data/assets/</code> 是生成的图片。备份数据即备份这两个位置。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import './style.scss'

defineOptions({ name: 'StudioHelp' })

/** 左侧锚点目录 */
const sections = [
  { id: 'sec-quickstart', label: '🚀 快速上手' },
  { id: 'sec-models', label: '🧠 模型配置详解' },
  { id: 'sec-faq', label: '❓ 常见问题 FAQ' }
]

const activeAnchor = ref('sec-quickstart')

const scrollTo = (id: string) => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

/** 滚动监听：高亮当前所在章节 */
const onScroll = () => {
  for (const sec of sections) {
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

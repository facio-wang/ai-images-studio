/**
 * 工作台概览文案（overview：home + onboarding + detail）
 * zh 值与页面原文逐字对应；服务状态条复用 common.service.*，任务类型复用 common.taskType.*
 */
export const overviewModule = {
  zh: {
    home: {
      title: '工作台',
      desc: '本地 AI 创作中台 · 今天已提交 {n} 个任务',
      replayGuide: '📖 重新查看引导',
      helpCenter: '帮助中心',
      taskCenter: '📋 任务中心',
      startGenerate: '🎨 开始生图',
      stat: {
        todayTasks: '今日任务数',
        todayTasksSub: '含生图与抠图任务',
        assetTotal: '资产总数',
        activeTasks: '排队 / 运行中',
        activeTasksSub: '进行中任务完成后自动入资产库'
      },
      vramLabel: 'GPU 显存',
      ramLabel: '系统内存',
      recentTitle: '最近作品',
      goAssets: '进入资产库 →',
      emptyRecent: '还没有作品，从生图或对话工作台开始吧',
      quickLinks: '快捷入口',
      entry: {
        chat: {
          name: '对话工作台',
          sub: '一句话完成处理'
        },
        generate: {
          name: '新建生图',
          sub: 'ComfyUI 文生图'
        },
        matting: {
          name: '抠图工具箱'
        },
        models: {
          name: '模型中心',
          sub: '底模 / LoRA / 翻译'
        }
      }
    },
    onboarding: {
      title: '🎉 欢迎使用 AI Images Studio',
      steps: {
        welcome: '欢迎',
        generate: '生图配置',
        translate: '翻译配置',
        done: '完成'
      },
      terms: {
        localRun: '本地运行',
        translate: '翻译',
        openaiCompat: 'OpenAI 兼容接口'
      },
      s1: {
        lead: '这是一个{local}的 AI 创作平台，所有模型、图片和数据库都保存在你自己的电脑上，不会上传到任何云端。',
        gen: '🎨 {term}：连接本机 ComfyUI，输入提示词生成图片',
        translate: '🌐 {term}：把中文提示词翻译成英文（需要一个 OpenAI 兼容接口）',
        matting: '✂️ {term}：一键去除图片背景',
        note: '下面用 2 分钟完成初始配置，随时可以跳过。'
      },
      s2: {
        lead: '生图依赖本机的 {comfy} 服务。请确认 ComfyUI 已启动，并核对服务地址：',
        addrLabel: 'ComfyUI 地址',
        addrPlaceholder: '127.0.0.1:8188 或 192.168.31.57:8188',
        syncBtn: '一键同步底模',
        syncHint: '把 ComfyUI 里已安装的底模列表同步到模型中心',
        note: '如果同步失败，多半是 ComfyUI 没启动或地址不对，可先跳过稍后在系统设置里修改。'
      },
      s3: {
        lead: '翻译功能需要一个 {api}。到「模型中心 → 翻译」新增一个翻译模型，需要填 3 个字段：',
        baseUrl: '{field}：API 服务地址，如 {url}。各家服务商都会提供，自建中转站则填中转站地址',
        apiKeyTip: '{field}：密钥，在服务商控制台申请，形如 {keySample}，注意保密',
        modelId: '{field}：要调用的模型名，如 {m1}、{m2}',
        addModelBtn: '去模型中心添加',
        note: '没有海外卡？可以用硅基流动、DeepSeek 等国内服务商，或自建中转站。详见帮助页。'
      },
      s4: {
        lead: '配置完成！随时可以回到工作台查看快捷入口。',
        note: '遇到问题？顶部导航的「帮助中心」有完整教程和常见问题解答。'
      },
      skip: '跳过引导',
      prev: '上一步',
      next: '下一步',
      startGenerate: '开始生图 →',
      syncDone: '同步完成：新增 {n} 个底模',
      syncFail: '同步失败，请确认 ComfyUI 已启动、地址正确'
    },
    detail: {
      title: '生成详情',
      failReason: '失败原因：{reason}',
      prompt: '提示词',
      actualPrompt: '实际发送提示词',
      negative: '反向提示词',
      model: '生图模型',
      size: '尺寸',
      sizeValue: '{w} × {h} · {n} 张',
      sampling: '采样',
      samplingValue: '{steps} 步 · CFG {cfg}',
      taskType: '任务类型',
      createdAt: '创建时间',
      outputAssets: '产物资产',
      viewOriginal: '⬇ 查看原图',
      retryTask: '⟳ 重试任务',
      zImageSuffix: '{model}（Z-Image 原生中文）',
      assetIdSep: '、'
    }
  },
  en: {
    home: {
      title: 'Workspace',
      desc: 'Local AI creation hub · {n} tasks submitted today',
      replayGuide: '📖 Replay setup guide',
      helpCenter: 'Help Center',
      taskCenter: '📋 Task Center',
      startGenerate: '🎨 Start generating',
      stat: {
        todayTasks: "Today's tasks",
        todayTasksSub: 'Includes generation and matting tasks',
        assetTotal: 'Total assets',
        activeTasks: 'Queued / running',
        activeTasksSub: 'Finished tasks are added to the asset library automatically'
      },
      vramLabel: 'GPU VRAM',
      ramLabel: 'System memory',
      recentTitle: 'Recent work',
      goAssets: 'Open asset library →',
      emptyRecent: 'Nothing here yet — start from the generation or chat workspace',
      quickLinks: 'Quick links',
      entry: {
        chat: {
          name: 'Chat workspace',
          sub: 'Get it done with one sentence'
        },
        generate: {
          name: 'New generation',
          sub: 'Text-to-image with ComfyUI'
        },
        matting: {
          name: 'Matting toolbox'
        },
        models: {
          name: 'Model center',
          sub: 'Checkpoints / LoRA / translation'
        }
      }
    },
    onboarding: {
      title: '🎉 Welcome to AI Images Studio',
      steps: {
        welcome: 'Welcome',
        generate: 'Generation setup',
        translate: 'Translation setup',
        done: 'Done'
      },
      terms: {
        localRun: 'local-first',
        translate: 'Translation',
        openaiCompat: 'OpenAI-compatible API'
      },
      s1: {
        lead:
          'This is a {local} AI creation platform — all models, images, and the database stay on your own computer and never get uploaded to the cloud.',
        gen: '🎨 {term}: create images from prompts with your local ComfyUI',
        translate: '🌐 {term}: translate Chinese prompts into English (needs an OpenAI-compatible API endpoint)',
        matting: '✂️ {term}: remove image backgrounds in one click',
        note: 'The initial setup below takes about 2 minutes, and you can skip it at any time.'
      },
      s2: {
        lead:
          'Generation depends on the {comfy} service on this machine. Make sure ComfyUI is running, then double-check the service address:',
        addrLabel: 'ComfyUI address',
        addrPlaceholder: '127.0.0.1:8188 or 192.168.31.57:8188',
        syncBtn: 'Sync checkpoints',
        syncHint: 'Sync the checkpoint list installed in ComfyUI to the Model Center',
        note:
          'If syncing fails, ComfyUI is probably not running or the address is wrong — skip it for now and fix it later in system settings.'
      },
      s3: {
        lead:
          'Translation needs an {api}. Go to "Model Center → Translation" and add a translation model. Three fields are required:',
        baseUrl:
          '{field}: the API base URL, e.g. {url}. Every provider offers one; for a self-hosted relay, enter the relay address instead.',
        apiKeyTip: '{field}: the secret key from your provider console, looks like {keySample}. Keep it confidential.',
        modelId: '{field}: the model to call, e.g. {m1} or {m2}',
        addModelBtn: 'Add one in Model Center',
        note:
          'No international card? Use domestic providers such as SiliconFlow or DeepSeek, or run your own relay. See the Help page for details.'
      },
      s4: {
        lead: 'All set! Head back to the workspace any time to use the quick links.',
        note: 'Stuck? The Help Center in the top navigation has full tutorials and answers to common questions.'
      },
      skip: 'Skip guide',
      prev: 'Back',
      next: 'Next',
      startGenerate: 'Start generating →',
      syncDone: 'Sync complete: {n} new checkpoints added',
      syncFail: 'Sync failed. Make sure ComfyUI is running and the address is correct.'
    },
    detail: {
      title: 'Generation details',
      failReason: 'Failure reason: {reason}',
      prompt: 'Prompt',
      actualPrompt: 'Prompt actually sent',
      negative: 'Negative prompt',
      model: 'Generation model',
      size: 'Size',
      sizeValue: '{w} × {h} · {n} images',
      sampling: 'Sampling',
      samplingValue: '{steps} steps · CFG {cfg}',
      taskType: 'Task type',
      createdAt: 'Created at',
      outputAssets: 'Output assets',
      viewOriginal: '⬇ View original',
      retryTask: '⟳ Retry task',
      zImageSuffix: '{model} (Z-Image, native Chinese support)',
      assetIdSep: ', '
    }
  }
} as { zh: Record<string, unknown>; en: Record<string, unknown> }

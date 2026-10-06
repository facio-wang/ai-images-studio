/**
 * 资产库 + 任务中心 + 帮助中心文案（assets + tasks + help）
 * 模板用 $t('studio.assets.xxx') / $t('studio.tasks.xxx') / $t('studio.help.xxx')，脚本用 t(...)
 * 共享动作/状态/类型词复用 studio.common.*（见 common.ts），此处不重复定义
 */
export const libraryModule = {
  zh: {
    assets: {
      title: '资产库',
      desc: '生图 / 抠图 / 上传产物统一存储与管理',
      uploadBtn: '⬆ 上传图片',
      storageMeta: '📦 {name} v{version}',
      totalCount: '资产总数 {n}',
      currentFilter: '当前筛选：{filter}',
      all: '全部',
      unnamed: '未命名',
      empty: '暂无资产',
      loadMore: '加载更多',
      loadFailed: '加载资产失败',
      deleteTitle: '删除确认',
      deleteConfirm: '确认删除资产 #{n}？磁盘文件将一并删除。',
      deleted: '已删除',
      manualUpload: '手工上传',
      uploadSuccess: '上传成功',
      uploadFailed: '上传失败'
    },
    tasks: {
      title: '任务中心',
      desc: '生图 / 抠图任务队列与执行状态 · 失败任务可手动重试',
      allStatus: '全部状态',
      table: {
        type: '类型',
        status: '状态',
        params: '参数摘要',
        results: '产物',
        duration: '耗时',
        retries: '重试',
        createdAt: '创建时间',
        actions: '操作'
      },
      failTooltip: '失败原因：{msg}（点击重试重新入队）',
      empty: '暂无任务',
      loadFailed: '加载任务列表失败',
      paramsModel: 'model: {model}',
      paramsAsset: ' · 资产 #{n}',
      defaultModel: '默认',
      unknownError: '未知错误',
      onlyFailedRetry: '仅失败任务可重试',
      requeued: '任务 #{n} 已重新入队',
      retryFailed: '重试失败'
    },
    help: {
      title: '帮助中心',
      desc: '从零开始的配置指南与常见问题解答',
      nav: {
        quickstart: '🚀 快速上手',
        models: '🧠 模型配置详解',
        faq: '❓ 常见问题 FAQ'
      },
      quickstart: {
        title: '🚀 快速上手：三步开始生图',
        step1Title: '启动 ComfyUI 并同步底模',
        step1Body1: '确保本机 ComfyUI 已运行（默认 ',
        step1Body2: '）。到「模型中心」点「同步 ComfyUI 底模」，已安装的底模会自动出现在底模分区。',
        step2Title: '选一个默认底模',
        step2Body: '在底模分区点击「设默认」，生图页会自动使用默认底模；也可以在生图页临时切换。',
        step3Title: '输入提示词开始生成',
        step3Body: '到「生图」页输入描述（支持先翻译成英文），设置尺寸与步数后提交。完成后图片自动进入资产库。'
      },
      models: {
        title: '🧠 模型配置详解',
        lead: '平台共有四类模型，全部在「模型中心」统一管理。前三类本机即可配置，翻译模型需要外部 API。',
        checkpointTitle: '底模（checkpoint）',
        checkpointBody:
          '文生图的主模型。推荐直接用「同步 ComfyUI 底模」一键导入，无需手填。也可以手动新增，名称需与 ComfyUI models/checkpoints 目录下的文件名一致。',
        loraTitle: 'LoRA',
        loraBody1: '风格微调模型。手动新增，名称与 ComfyUI models/loras 目录下的文件名一致，附加信息可标注触发词，如 ',
        loraBody2: '。',
        mattingTitle: '抠图（matting）',
        mattingBody: '背景移除模型（如 bria-rmbg、birefnet）。首次使用时会自动下载到本机 data 目录，无需 API。',
        translateTitle: '翻译（translate）— 重点',
        translateBody1: '翻译模型通过 ',
        translateBold: 'OpenAI 兼容接口',
        translateBody2: '调用大模型完成中译英，新增时需要填 3 个字段：',
        fieldTable: {
          field: '字段',
          what: '是什么',
          where: '从哪获取',
          baseUrlWhat: 'API 服务根地址',
          baseUrlWhere1: '服务商文档提供，通常以 ',
          baseUrlWhere2: ' 结尾',
          apiKeyWhat: '访问密钥，形如 sk-...',
          apiKeyWhere: '服务商控制台「API Keys」页面创建',
          modelIdWhat: '要调用的具体模型名',
          modelIdWhere: '服务商模型列表页，如 gpt-4o-mini'
        },
        providers: {
          title: '常见服务商示例',
          headProvider: '服务商',
          headModelId: 'model_id 示例',
          openai: 'OpenAI 官方',
          siliconflow: '硅基流动',
          relay: '自建中转站',
                relayUrl: 'https://你的中转域名/v1',
          relayModels: '看中转站支持的模型列表'
        },
        note: '任何宣称「OpenAI 兼容」的服务都可以用。密钥只保存在本机数据库中。'
      },
      faq: {
        title: '❓ 常见问题 FAQ',
        q1: 'ComfyUI 连不上怎么办？',
        a1p1:
          '依次检查：① ComfyUI 是否已启动（浏览器能打开 http://127.0.0.1:8188 即正常）；② 地址端口是否正确，ComfyUI 在其他机器时用那台机器的 IP（如 ',
        a1p2: '），且启动时需要加 ',
        a1p3: '；③ 防火墙是否放行 8188 端口。',
        q2: '翻译报 401 是什么意思？',
        a2: '401 = 密钥无效。检查：① api_key 是否复制完整（没有多余空格）；② 密钥是否已过期或被禁用；③ 账户是否有余额。到「模型中心 → 翻译 → 编辑」更新密钥即可。',
        q3: '抠图模型下载失败怎么办？',
        a3p1:
          '抠图模型首次使用时从 GitHub/HuggingFace 下载，网络不通会失败。可手动下载模型文件（如 u2netp.onnx）放到本机 ',
        a3p2: ' 目录后重试。',
        q4: '生图任务一直排队？',
        a4: '任务由本机 worker 逐个执行，ComfyUI 正在出图时新任务会排队。若长时间不动，到「任务中心」查看任务错误信息，或检查 ComfyUI 是否卡死。',
        q5: '数据都存在哪里？',
        a5p1: '全部在本机：',
        a5p2: ' 是数据库（模型配置、任务记录），',
        a5p3: ' 是生成的图片。备份数据即备份这两个位置。'
      }
    }
  },
  en: {
    assets: {
      title: 'Asset Library',
      desc: 'Unified storage and management of generation / matting / upload outputs',
      uploadBtn: '⬆ Upload image',
      storageMeta: '📦 {name} v{version}',
      totalCount: 'Total assets: {n}',
      currentFilter: 'Current filter: {filter}',
      all: 'All',
      unnamed: 'Untitled',
      empty: 'No assets yet',
      loadMore: 'Load more',
      loadFailed: 'Failed to load assets',
      deleteTitle: 'Confirm deletion',
      deleteConfirm: 'Delete asset #{n}? The file on disk will be removed as well.',
      deleted: 'Deleted',
      manualUpload: 'Manual upload',
      uploadSuccess: 'Uploaded successfully',
      uploadFailed: 'Upload failed'
    },
    tasks: {
      title: 'Task Center',
      desc: 'Queue and execution status for generation / matting tasks · failed tasks can be retried manually',
      allStatus: 'All statuses',
      table: {
        type: 'Type',
        status: 'Status',
        params: 'Parameters',
        results: 'Outputs',
        duration: 'Duration',
        retries: 'Retries',
        createdAt: 'Created at',
        actions: 'Actions'
      },
      failTooltip: 'Failure reason: {msg} (click Retry to re-enqueue)',
      empty: 'No tasks yet',
      loadFailed: 'Failed to load tasks',
      paramsModel: 'Model: {model}',
      paramsAsset: ' · Asset #{n}',
      defaultModel: 'Default',
      unknownError: 'Unknown error',
      onlyFailedRetry: 'Only failed tasks can be retried',
      requeued: 'Task #{n} re-enqueued',
      retryFailed: 'Retry failed'
    },
    help: {
      title: 'Help Center',
      desc: 'A from-zero setup guide with answers to common questions',
      nav: {
        quickstart: '🚀 Quick start',
        models: '🧠 Model configuration',
        faq: '❓ FAQ'
      },
      quickstart: {
        title: '🚀 Quick start: three steps to your first image',
        step1Title: 'Start ComfyUI and sync base models',
        step1Body1: 'Make sure ComfyUI is running on this machine (default ',
        step1Body2:
          '). Open the Model Center and click "Sync ComfyUI base models"; installed base models will appear in the base model section automatically.',
        step2Title: 'Pick a default base model',
        step2Body:
          'Click "Set default" in the base model section and the Generate page will use it automatically; you can still switch models temporarily on the Generate page.',
        step3Title: 'Enter a prompt and start generating',
        step3Body:
          'Go to the Generate page, type a description (it can be translated into English first), set the size and steps, then submit. Finished images are added to the Asset Library automatically.'
      },
      models: {
        title: '🧠 Model configuration in detail',
        lead:
          'The platform has four model categories, all managed in one place in the Model Center. The first three run fully locally; the translation model needs an external API.',
        checkpointTitle: 'Base model (checkpoint)',
        checkpointBody:
          'The main model for text-to-image. The recommended way is a one-click import via "Sync ComfyUI base models" — no manual typing needed. You can also add one manually; the name must match a file name in the ComfyUI models/checkpoints directory.',
        loraTitle: 'LoRA',
        loraBody1:
          'A style fine-tuning model. Add it manually; the name must match a file name in the ComfyUI models/loras directory, and the extra info can note trigger words, e.g. ',
        loraBody2: '.',
        mattingTitle: 'Matting',
        mattingBody:
          'Background removal models (e.g. bria-rmbg, birefnet). Downloaded automatically into the local data directory on first use; no API needed.',
        translateTitle: 'Translation (translate) — key points',
        translateBody1: 'The translation model calls an LLM through an ',
        translateBold: 'OpenAI-compatible API',
        translateBody2:
          ' to translate Chinese prompts into English. Three fields are required when adding one:',
        fieldTable: {
          field: 'Field',
          what: 'What it is',
          where: 'Where to get it',
          baseUrlWhat: 'Root URL of the API service',
          baseUrlWhere1: 'Provided in the provider docs, usually ends with ',
          baseUrlWhere2: '.',
          apiKeyWhat: 'Access key, looks like sk-...',
          apiKeyWhere: 'Created on the "API Keys" page of the provider console',
          modelIdWhat: 'The specific model name to call',
          modelIdWhere: 'Listed on the provider model page, e.g. gpt-4o-mini'
        },
        providers: {
          title: 'Common provider examples',
          headProvider: 'Provider',
          headModelId: 'model_id examples',
          openai: 'OpenAI (official)',
          siliconflow: 'SiliconFlow',
          relay: 'Self-hosted relay',
                relayUrl: 'https://your-relay-host/v1',
          relayModels: 'Check the model list your relay supports'
        },
        note:
          'Any service that claims to be "OpenAI-compatible" will work. Keys are stored only in the local database.'
      },
      faq: {
        title: '❓ FAQ',
        q1: 'What if ComfyUI cannot be connected?',
        a1p1:
          'Check in order: ① ComfyUI is running (opening http://127.0.0.1:8188 in the browser means it is up); ② the address and port are correct — when ComfyUI runs on another machine, use the IP of that machine (e.g. ',
        a1p2: ') and add ',
        a1p3: ' when starting it; ③ port 8188 is allowed through the firewall.',
        q2: 'What does a 401 error from translation mean?',
        a2:
          '401 = invalid key. Check: ① the api_key was copied in full (no extra spaces); ② the key has not expired or been disabled; ③ the account still has balance. Update the key under "Model Center → Translation → Edit".',
        q3: 'What if a matting model fails to download?',
        a3p1:
          'Matting models are downloaded from GitHub/HuggingFace on first use; this fails when the network is unreachable. You can download the model file manually (e.g. u2netp.onnx) and place it in the local ',
        a3p2: ' directory, then retry.',
        q4: 'Why is a generation task stuck in the queue?',
        a4:
          'Tasks run one by one in a local worker; new tasks wait in the queue while ComfyUI is rendering. If nothing progresses for a long time, check the task error in the Task Center, or verify that ComfyUI is not stuck.',
        q5: 'Where is the data stored?',
        a5p1: 'Everything is stored locally: ',
        a5p2: ' is the database (model config and task records), ',
        a5p3:
          ' holds the generated images. Backing up your data means backing up these two locations.'
      }
    }
  }
} as { zh: Record<string, unknown>; en: Record<string, unknown> }

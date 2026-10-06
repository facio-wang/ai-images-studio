/** 抠图工具箱 + 模型中心文案（matting + models） */
export const creationModule = {
  zh: {
    matting: {
      title: '抠图工具箱',
      desc: '本地推理去背景 · 输出透明底 PNG · 模型来自「模型中心」',
      modelTitle: '抠图模型',
      option: {
        u2net: 'u2net（轻量 · CPU 友好 · 推荐）',
        u2netp: 'u2netp（极速 · 低配设备）',
        bria: 'bria-rmbg（效果好 · 需 GPU/强 CPU）',
        birefnet: 'birefnet-general（高精度发丝边缘 · 需强算力）'
      },
      upload: {
        title: '上传图片',
        text: '拖拽文件到此处，或',
        click: '点击选择',
        formats: '支持 PNG / JPG / WebP'
      },
      sourcePreviewAlt: '源图预览',
      pickExisting: '或选择已有资产',
      emptyAssets: '资产库暂无可用图片',
      submitBtn: '✂️ 提交抠图任务',
      compare: {
        title: '处理前后对比',
        hint: '拖动滑块查看抠图效果',
        before: '◀ 原图',
        after: '抠图结果（资产 #{n}）▶'
      },
      wait: {
        hint: '低配设备 / 大图推理可能需要几分钟，可放心等待'
      },
      downloadResult: '⬇ 下载结果',
      again: '再来一张',
      emptyResult: '上传图片或选择资产后提交，抠图结果将展示在这里',
      assetLabel: '资产 #{n}',
      phase: {
        submitting: '正在提交…',
        queued: '排队等待推理…',
        running: 'AI 推理中，请稍候…',
        loading: '加载结果…'
      },
      message: {
        submitFailed: '提交抠图任务失败',
        noAsset: '任务完成但未产出资产',
        done: '抠图完成（耗时 {n}s）',
        failed: '抠图任务失败'
      }
    },
    models: {
      title: '模型中心',
      desc: '所有模块（生图 / 翻译 / 抠图）统一从这里管理，各功能页仅选择引用',
      helpBtn: '📖 配置帮助',
      syncBtn: '🔄 同步 ComfyUI 底模',
      addBtn: '＋ 新增模型',
      stat: {
        count: '{category}数量',
        total: '模型总数 {total} · 底模 {checkpoint} · LoRA {lora} · 翻译 {translate} · 抠图 {matting}',
        enabled: '启用中',
        enabledHint: '各分区默认模型各 1 个，功能页取默认执行',
        endpoint: 'ComfyUI 端点',
        endpointHint: '底模列表可从 ComfyUI 一键同步'
      },
      category: {
        checkpoint: '底模',
        lora: 'LoRA',
        translate: '翻译',
        matting: '抠图'
      },
      table: {
        name: '模型名称',
        default: '默认',
        category: '类别',
        meta: '附加信息',
        api: '接口',
        model: '模型',
        key: '密钥',
        enabled: '启用',
        actions: '操作',
        setDefault: '设默认',
        edit: '编辑'
      },
      dialog: {
        addTitle: '新增模型',
        editTitle: '编辑模型 - {name}',
        name: '名称',
        category: '类别',
        baseUrl: '接口地址',
        apiKey: 'API Key',
        modelId: '模型 ID',
        remark: '备注',
        meta: '附加信息',
        confirmAdd: '确认新增',
        saveEdit: '保存修改'
      },
      placeholder: {
        name: '模型名称，如 dreamshaperXL',
        baseUrl: 'https://api.openai.com/v1 或兼容接口地址',
        apiKeyTip: '服务商控制台申请的密钥，如 sk-...',
        apiKeyKeep: '留空则保持原密钥不变',
        modelId: 'gpt-4o-mini / deepseek-chat 等',
        remark: '其他附加信息 JSON（可留空）',
        meta: "JSON，如 {'{'}\"file\": \"xxx.safetensors\"{'}'}（可留空）"
      },
      tip: {
        translate:
          '接口地址是提供翻译服务的 API 根地址，API Key 在服务商控制台申请（如 OpenAI 官方、硅基流动、DeepSeek 或自建中转站），模型 ID 是要调用的具体模型名。详见',
        helpLink: '帮助页'
      },
      notSet: '未设置',
      message: {
        loadFailed: '加载模型列表失败',
        enabled: '已启用',
        disabled: '已停用',
        updateFailed: '更新失败',
        setDefault: '已将「{name}」设为{category}默认',
        setDefaultFailed: '设置默认失败',
        deleteConfirm: '确认删除模型「{name}」？该操作不可恢复。',
        deleteTitle: '删除确认',
        deleted: '已删除',
        nameRequired: '请输入模型名称',
        translateRequired: '翻译模型需要填写接口地址和模型 ID',
        remarkInvalid: '备注不是合法 JSON，已忽略',
        metaInvalid: '附加信息不是合法 JSON，已忽略',
        metaInvalidKeep: '附加信息不是合法 JSON，已保持原值',
        addSuccess: '新增成功',
        addFailed: '新增失败（可能与已有模型重名或缺少翻译配置）',
        saveSuccess: '已保存',
        saveFailed: '保存失败',
        syncSuccess: '已触发底模同步',
        syncFailed: '同步失败（ComfyUI 不可达？）'
      }
    }
  },
  en: {
    matting: {
      title: 'Matting toolbox',
      desc: 'Local background removal · Outputs transparent PNG · Models come from the Model Center',
      modelTitle: 'Matting model',
      option: {
        u2net: 'u2net (Lightweight · CPU friendly · Recommended)',
        u2netp: 'u2netp (Fastest · For low-end devices)',
        bria: 'bria-rmbg (High quality · Needs GPU/strong CPU)',
        birefnet: 'birefnet-general (High-precision hair-edge detail · Needs strong hardware)'
      },
      upload: {
        title: 'Upload image',
        text: 'Drag a file here, or',
        click: 'click to browse',
        formats: 'Supports PNG / JPG / WebP'
      },
      sourcePreviewAlt: 'Source image preview',
      pickExisting: 'Or pick an existing asset',
      emptyAssets: 'No images available in the asset library yet',
      submitBtn: '✂️ Submit matting task',
      compare: {
        title: 'Before / after comparison',
        hint: 'Drag the slider to check the matting result',
        before: '◀ Original',
        after: 'Matting result (asset #{n}) ▶'
      },
      wait: {
        hint: 'On low-end devices or large images, inference may take a few minutes — feel free to wait'
      },
      downloadResult: '⬇ Download result',
      again: 'Another one',
      emptyResult: 'Upload an image or pick an asset and submit — the matting result will show up here',
      assetLabel: 'Asset #{n}',
      phase: {
        submitting: 'Submitting…',
        queued: 'Queued, waiting for inference…',
        running: 'AI inference in progress, please wait…',
        loading: 'Loading result…'
      },
      message: {
        submitFailed: 'Failed to submit matting task',
        noAsset: 'Task finished but produced no asset',
        done: 'Matting done (took {n}s)',
        failed: 'Matting task failed'
      }
    },
    models: {
      title: 'Model center',
      desc: 'All modules (generation / translation / matting) are managed here; feature pages only reference them',
      helpBtn: '📖 Config guide',
      syncBtn: '🔄 Sync base models from ComfyUI',
      addBtn: '＋ Add model',
      stat: {
        count: '{category} count',
        total: 'Total {total} · Base models {checkpoint} · LoRA {lora} · Translation {translate} · Matting {matting}',
        enabled: 'Enabled',
        enabledHint: 'Each section has one default model, which feature pages use by default',
        endpoint: 'ComfyUI endpoint',
        endpointHint: 'The base model list can be synced from ComfyUI in one click'
      },
      category: {
        checkpoint: 'Base model',
        lora: 'LoRA',
        translate: 'Translation',
        matting: 'Matting'
      },
      table: {
        name: 'Name',
        default: 'Default',
        category: 'Category',
        meta: 'Metadata',
        api: 'API',
        model: 'Model',
        key: 'Key',
        enabled: 'Enabled',
        actions: 'Actions',
        setDefault: 'Set default',
        edit: 'Edit'
      },
      dialog: {
        addTitle: 'Add model',
        editTitle: 'Edit model - {name}',
        name: 'Name',
        category: 'Category',
        baseUrl: 'API URL',
        apiKey: 'API Key',
        modelId: 'Model ID',
        remark: 'Remark',
        meta: 'Metadata',
        confirmAdd: 'Add',
        saveEdit: 'Save changes'
      },
      placeholder: {
        name: 'Model name, e.g. dreamshaperXL',
        baseUrl: 'https://api.openai.com/v1 or a compatible API URL',
        apiKeyTip: 'The key from your provider console, e.g. sk-...',
        apiKeyKeep: 'Leave empty to keep the current key',
        modelId: 'gpt-4o-mini / deepseek-chat, etc.',
        remark: 'Extra metadata JSON (optional)',
        meta: "JSON, e.g. {'{'}\"file\": \"xxx.safetensors\"{'}'} (optional)"
      },
      tip: {
        translate:
          'The API URL is the root URL of the translation service API. The API key is obtained from the provider console (OpenAI, SiliconFlow, DeepSeek, or a self-hosted relay), and the model ID is the specific model to call. See the',
        helpLink: 'Help page'
      },
      notSet: 'Not set',
      message: {
        loadFailed: 'Failed to load models',
        enabled: 'Enabled',
        disabled: 'Disabled',
        updateFailed: 'Update failed',
        setDefault: '"{name}" is now the default {category}',
        setDefaultFailed: 'Failed to set default',
        deleteConfirm: 'Delete model "{name}"? This cannot be undone.',
        deleteTitle: 'Delete confirmation',
        deleted: 'Deleted',
        nameRequired: 'Please enter a model name',
        translateRequired: 'API URL and model ID are required for translation models',
        remarkInvalid: 'Remark is not valid JSON; it was ignored',
        metaInvalid: 'Metadata is not valid JSON; it was ignored',
        metaInvalidKeep: 'Metadata is not valid JSON; the original value was kept',
        addSuccess: 'Model added',
        addFailed: 'Failed to add (the name may already exist, or the translation config is incomplete)',
        saveSuccess: 'Saved',
        saveFailed: 'Save failed',
        syncSuccess: 'Base model sync triggered',
        syncFailed: 'Sync failed (is ComfyUI unreachable?)'
      }
    }
  }
} as { zh: Record<string, unknown>; en: Record<string, unknown> }

/**
 * 对话工作台文案（chat）
 * 模板用 $t('studio.chat.xxx')，脚本用 t('studio.chat.xxx')
 * 服务横幅/一键启动、动作、任务类型词复用 studio.common.*（见 common.ts）
 */
export const chatModule = {
  zh: {
    chat: {
      title: '对话工作台',
      desc: '一句话完成生图 / 抠图 / 查询，产物自动入资产库',
      newSession: '＋ 新建会话',
      tip: '💡 对话模式 · 所有图片处理都可以在这里用一句话完成',
      tipRight: '生图 · 抠图 · 资产/任务查询',
      avaMe: '我',
      assetAlt: '资产#{n}',
      retryTask: '⟳ 重试任务 #{n}',
      taskWaiting: '任务 #{n} 执行中，完成后自动展示产物…',
      emptyHint: '开始与 AI 对话，例如「生成一张赛博朋克城市夜景」',
      inputPlaceholder: '描述你想做的图片处理，例如：生成一张赛博朋克风格的城市夜景…',
      send: '发送 ➤',
      sessionsTitle: '历史会话',
      sessionItem: '会话 #{n} · {title}',
      noSessions: '暂无历史会话',
      deleteSession: '删除会话',
      confirmDelete: '删除会话 #{n} 将同时移除其消息记录；图片资产会保留在资产库中，可在资产库内删除。',
      sessionDeleted: '会话已删除',
      assetsTitle: '会话产物',
      unnamed: '未命名',
      noAssets: '本会话暂无产物',
      taskFailedDetail: '任务 #{n} 失败：{msg}',
      sendFailed: '发送失败',
      taskRequeued: '任务 #{n} 已重新入队',
      retryFailed: '重试失败',
      loadMessagesFailed: '加载会话消息失败'
    }
  },
  en: {
    chat: {
      title: 'Chat workspace',
      desc: 'Generation, matting and queries in one sentence; outputs go straight to the asset library',
      newSession: '＋ New session',
      tip: '💡 Chat mode · every image task can be done here in a single sentence',
      tipRight: 'Generation · Matting · Asset/task queries',
      avaMe: 'Me',
      assetAlt: 'Asset #{n}',
      retryTask: '⟳ Retry task #{n}',
      taskWaiting: 'Task #{n} is running; results will appear here when done…',
      emptyHint: 'Start chatting with the AI, e.g. "Generate a cyberpunk city nightscape"',
      inputPlaceholder: 'Describe the image task you want, e.g. generate a cyberpunk-style city nightscape…',
      send: 'Send ➤',
      sessionsTitle: 'Session history',
      sessionItem: 'Session #{n} · {title}',
      noSessions: 'No sessions yet',
      deleteSession: 'Delete session',
      confirmDelete:
        'Deleting session #{n} also removes its messages; generated images stay in the asset library and can be deleted there.',
      sessionDeleted: 'Session deleted',
      assetsTitle: 'Session outputs',
      unnamed: 'Untitled',
      noAssets: 'No outputs in this session yet',
      taskFailedDetail: 'Task #{n} failed: {msg}',
      sendFailed: 'Failed to send the message',
      taskRequeued: 'Task #{n} re-queued',
      retryFailed: 'Retry failed',
      loadMessagesFailed: 'Failed to load chat messages'
    }
  }
} as { zh: Record<string, unknown>; en: Record<string, unknown> }

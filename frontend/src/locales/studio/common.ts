/**
 * Studio 共享文案（所有业务页面公用的动作/状态/类型词）
 * 每个模块导出 { zh, en } 两棵子树，由 index.ts 合并到 i18n 的 studio.* 命名空间
 */
export const commonModule = {
  zh: {
    common: {
      actions: {
        confirm: '确认',
        cancel: '取消',
        delete: '删除',
        refresh: '刷新',
        download: '下载',
        preview: '预览',
        search: '搜索',
        save: '保存',
        close: '关闭',
        retry: '重试',
        detail: '详情',
        submit: '提交',
        backHome: '返回工作台'
      },
      taskType: {
        generate: '生图',
        matting: '抠图',
        upload: '上传'
      },
      taskStatus: {
        queued: '排队中',
        running: '运行中',
        done: '已完成',
        failed: '失败'
      },
      taskFailedMsg: '任务执行失败',
      waitedFor: '已等待 {n}',
      service: {
        label: '生图服务',
        fullName: '生图服务（ComfyUI）',
        running: '运行中',
        stopped: '未启动',
        starting: '启动中',
        detecting: '正在检测服务状态…',
        version: '版本',
        statusLabel: '状态',
        queue: '队列',
        queueDetail: '运行 {running} · 排队 {pending}',
        address: '地址',
        gpuIdle: '空闲',
        startBtn: '⚡ 一键启动',
        startingBtn: '启动中 {n}s…',
        startHint:
          '生图/对话生图功能暂不可用。可一键拉起启动脚本（需后端与 ComfyUI 同机），或在 Win11 宿主机手动启动。',
        manualHint: '生图/对话生图功能暂不可用，请在 Win11 宿主机启动 ComfyUI（端口 8188）',
        chatBannerTitle: '生图服务（ComfyUI 8188）未启动：发送生图/抠图请求会直接得到失败提示',
        chatBannerDesc: '请在 Win11 宿主机启动 ComfyUI 后重试；查询类对话不受影响。',
        refreshTip: '刷新状态',
        triggerTip: '生图服务（ComfyUI）状态'
      }
    }
  },
  en: {
    common: {
      actions: {
        confirm: 'Confirm',
        cancel: 'Cancel',
        delete: 'Delete',
        refresh: 'Refresh',
        download: 'Download',
        preview: 'Preview',
        search: 'Search',
        save: 'Save',
        close: 'Close',
        retry: 'Retry',
        detail: 'Details',
        submit: 'Submit',
        backHome: 'Back to Workspace'
      },
      taskType: {
        generate: 'Generation',
        matting: 'Matting',
        upload: 'Upload'
      },
      taskStatus: {
        queued: 'Queued',
        running: 'Running',
        done: 'Done',
        failed: 'Failed'
      },
      taskFailedMsg: 'Task execution failed',
      waitedFor: 'Waited {n}',
      service: {
        label: 'Engine',
        fullName: 'Generation Engine (ComfyUI)',
        running: 'Running',
        stopped: 'Stopped',
        starting: 'Starting',
        detecting: 'Detecting service status…',
        version: 'Version',
        statusLabel: 'Status',
        queue: 'Queue',
        queueDetail: 'Running {running} · Pending {pending}',
        address: 'Endpoint',
        gpuIdle: 'free',
        startBtn: '⚡ Quick Start',
        startingBtn: 'Starting {n}s…',
        startHint:
          'Generation is unavailable. Launch the start script with one click (backend must share the host with ComfyUI), or start ComfyUI manually.',
        manualHint:
          'Generation is unavailable. Please start ComfyUI on the Windows host (port 8188).',
        chatBannerTitle:
          'Generation engine (ComfyUI 8188) is offline: image/matting requests will fail right away',
        chatBannerDesc: 'Start ComfyUI on the Windows host and retry; query chats are unaffected.',
        refreshTip: 'Refresh status',
        triggerTip: 'Generation engine (ComfyUI) status'
      }
    }
  }
}

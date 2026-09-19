// requireReLogin: true // 需要重新登录

interface UpgradeLog {
  version: string // 版本号
  title: string // 更新标题
  date: string // 更新日期
  detail?: string[] // 更新内容
  requireReLogin?: boolean // 是否需要重新登录
}

export const upgradeLogList = ref<UpgradeLog[]>([
  {
    version: 'v1.0.1',
    title: '',
    date: '2025-11-02',
    detail: ['接入微信小程序扫码登录']
  },
  {
    version: 'v1.0.0',
    title: '',
    date: '2025-06-17',
    detail: ['项目初始化', '基础功能接入', '账号登录实现', '个人中心模块', '管理员模块']
  }
])

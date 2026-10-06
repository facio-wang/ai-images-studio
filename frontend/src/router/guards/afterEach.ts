import { useSettingStore } from '@/store/modules/setting'
import { useWorktabStore } from '@/store/modules/worktab'
import { Router } from 'vue-router'
import NProgress from 'nprogress'

/**
 * 页签标题自愈：i18n 之前持久化的页签存的是硬编码中文标题，
 * 按当前路由表的 meta.title（i18n key）刷新，老用户升级后页签自动恢复可翻译状态
 */
function reconcileWorktabTitles(router: Router) {
  const store = useWorktabStore()
  if (!store.opened?.length) return
  const titleMap = new Map(router.getRoutes().map((r) => [String(r.name), r.meta?.title as string]))
  store.opened.forEach((tab) => {
    const latest = titleMap.get(String(tab.name))
    if (latest && tab.title !== latest) tab.title = latest
  })
}

/** 路由全局后置守卫 */
export function setupAfterEachGuard(router: Router) {
  router.afterEach(() => {
    if (useSettingStore().showNprogress) NProgress.done()
    reconcileWorktabTitles(router)
  })
}

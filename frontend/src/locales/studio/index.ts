/**
 * Studio i18n 模块聚合器：
 * 每个业务模块导出 { zh, en } 子树，这里合并为 studio.* 命名空间，
 * 由 ../index.ts 在语言包加载后合并进 i18n 全局消息。
 */
import { commonModule } from './common'
import { overviewModule } from './overview'
import { chatModule } from './chat'
import { generateModule } from './generate'
import { creationModule } from './creation'
import { libraryModule } from './library'
import { authModule } from './auth'
import { settingsModule } from './settings'
import { personalModule } from './personal'
import { trainModule } from './train'

const zh = {
  ...commonModule.zh,
  ...overviewModule.zh,
  ...chatModule.zh,
  ...generateModule.zh,
  ...creationModule.zh,
  ...libraryModule.zh,
  ...authModule.zh,
  ...settingsModule.zh,
  ...personalModule.zh,
  ...trainModule.zh
}

const en = {
  ...commonModule.en,
  ...overviewModule.en,
  ...chatModule.en,
  ...generateModule.en,
  ...creationModule.en,
  ...libraryModule.en,
  ...authModule.en,
  ...settingsModule.en,
  ...personalModule.en,
  ...trainModule.en
}

export const studioMessages: Record<string, Record<string, unknown>> = { zh, en }

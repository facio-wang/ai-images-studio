import { createI18n } from 'vue-i18n'
import type { I18n, I18nOptions } from 'vue-i18n'
import { LanguageEnum } from '@/enums/appEnum'
import { getSystemStorage } from '@/utils/storage'
import { studioMessages } from './studio'
import zhFramework from './langs/zh.json'
import enFramework from './langs/en.json'

// 语言选项
export const languageOptions = [
  { value: LanguageEnum.ZH, label: '简体中文' },
  { value: LanguageEnum.EN, label: 'English' }
]

// 获取初始语言
const getDefaultLanguage = (): LanguageEnum => {
  const sys = getSystemStorage()
  if (!sys) return LanguageEnum.ZH

  try {
    const { user } = JSON.parse(sys)
    return user?.language || LanguageEnum.ZH
  } catch (error) {
    console.error('获取初始语言失败', error)
    return LanguageEnum.ZH
  }
}

// 语言包同步静态导入：框架文案（JSON）+ 业务文案（studio TS 模块）在 i18n 创建时就位，
// 避免异步注入导致菜单/面包屑首屏渲染出原始 key
const messages = {
  [LanguageEnum.ZH]: { ...zhFramework, studio: studioMessages[LanguageEnum.ZH] ?? {} },
  [LanguageEnum.EN]: { ...enFramework, studio: studioMessages[LanguageEnum.EN] ?? {} }
}

const i18nOptions: I18nOptions = {
  locale: getDefaultLanguage(),
  legacy: false,
  globalInjection: true,
  fallbackLocale: LanguageEnum.ZH,
  messages
}

const i18n: I18n = createI18n(i18nOptions)

interface Translation {
  (key: string): string
}

export const $t = i18n.global.t as Translation

export default i18n

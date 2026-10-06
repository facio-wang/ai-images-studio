/** 登录页文案（login）。模板用 $t('studio.login.xxx')，脚本用 t('studio.login.xxx') */
export const authModule = {
  zh: {
    login: {
      title: '登录工作台',
      subTitle: '请输入访问令牌（Token）以进入创作中台 · 仅限局域网授权用户',
      tokenPlaceholder: '请输入访问令牌（服务端 .env 中的 STUDIO_TOKEN）',
      submit: '登录工作台 →',
      footerToken: 'Token 配置于服务端 .env 的 STUDIO_TOKEN',
      footerLocal: '本地会话 · 令牌仅存于浏览器 localStorage',
      tokenRequired: '请输入访问令牌',
      tokenInvalid: '令牌无效或服务不可达，请检查后重试',
      successTitle: '登录成功',
      successMessage: '欢迎回到 AI Images Studio!'
    }
  },
  en: {
    login: {
      title: 'Sign in to the workspace',
      subTitle: 'Enter your access token to enter the creation hub · LAN-authorized users only',
      tokenPlaceholder: 'Enter the access token (STUDIO_TOKEN in the server .env)',
      submit: 'Sign in to the workspace →',
      footerToken: 'The token is configured as STUDIO_TOKEN in the server .env',
      footerLocal: 'Local session · the token is kept only in browser localStorage',
      tokenRequired: 'Please enter the access token',
      tokenInvalid: 'Invalid token or service unreachable. Please check and try again',
      successTitle: 'Signed in',
      successMessage: 'Welcome back to AI Images Studio!'
    }
  }
} as { zh: Record<string, unknown>; en: Record<string, unknown> }

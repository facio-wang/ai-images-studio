/**
 * 路由别名，方便快速找到页面，同时可以用作路由跳转
 */
export enum RoutesAlias {
  Home = '/index/index', // 布局容器
  Login = '/auth/login', // 登录
  Register = '/auth/register', // 注册
  ForgetPassword = '/auth/forget-password', // 忘记密码
  FeishuCallback = '/auth/feishu/callback', // 飞书登录回调
  Exception404 = '/exception/404', // 404
  Welcome = '/creation/home', // 工作台概览页（登录后落地页）
  Personal = '/personal' // 个人中心（从头像入口进入，不在侧边栏）
}

// 主页路由
export const HOME_PAGE = RoutesAlias.Welcome

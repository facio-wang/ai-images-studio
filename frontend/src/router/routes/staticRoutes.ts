import { AppRouteRecordRaw } from '../utils/utils'
import { RoutesAlias, HOME_PAGE } from '../routesAlias'
import Home from '@views/index/index.vue'

/**
 * 静态路由配置
 * 不需要权限就能访问的路由
 */
export const staticRoutes: AppRouteRecordRaw[] = [
  {
    path: '/',
    redirect: HOME_PAGE
  },
  {
    path: RoutesAlias.Login,
    name: 'Login',
    component: () => import('@views/auth/login/index.vue'),
    meta: { title: 'menus.login.title', isHideTab: true, setTheme: true }
  },
  {
    path: RoutesAlias.Register,
    name: 'Register',
    component: () => import('@views/auth/register/index.vue'),
    meta: { title: 'menus.register.title', isHideTab: true, noLogin: true, setTheme: true }
  },
  {
    path: RoutesAlias.ForgetPwd,
    name: 'ForgetPwd',
    component: () => import('@views/auth/forget-password/index.vue'),
    meta: { title: 'menus.forgetPassword.title', isHideTab: true, noLogin: true, setTheme: true }
  },
  {
    // 飞书扫码登录回调：后端重定向携带 token/error 到此页
    path: RoutesAlias.FeishuCallback,
    name: 'FeishuCallback',
    component: () => import('@views/auth/feishu-callback/index.vue'),
    meta: { title: '飞书登录', isHideTab: true, noLogin: true, setTheme: true }
  },
  {
    path: '/exception',
    component: Home,
    name: 'Exception',
    meta: { title: 'menus.exception.title' },
    children: [
      {
        path: '/:catchAll(.*)',
        name: 'Exception404',
        component: () => import('@views/exception/404/index.vue'),
        meta: { title: '404' }
      }
    ]
  },
  {
    path: '/outside',
    component: Home,
    name: 'Outside',
    meta: { title: 'menus.outside.title' },
    children: [
      {
        path: '/outside/iframe/:path',
        name: 'Iframe',
        component: () => import('@/views/outside/Iframe.vue'),
        meta: { title: 'iframe' }
      }
    ]
  },
  {
    // 个人中心：从头像下拉菜单进入，不显示在侧边栏菜单
    path: RoutesAlias.Personal,
    component: Home,
    name: 'PersonalLayout',
    meta: { title: '个人中心' },
    children: [
      {
        path: '',
        name: 'Personal',
        component: () => import('@views/personal/index.vue'),
        meta: { title: '个人中心' }
      }
    ]
  }
]

import { AppRouteRecord } from '@/types/router'

/**
 * 异步路由（前端控制模式菜单）
 *
 * AI Images Studio：后端无 /admin/menu/list（VITE_ACCESS_MODE=frontend），
 * 菜单由此处提供，经 menuDataToRouter → registerDynamicRoutes 注册。
 *
 * 分组：创作（工作台/对话工作台/生图/抠图）| 管理（模型中心/资产库/任务中心）| 系统（系统设置）
 */

// 菜单图标（iconfont-sys 字符）
const ICONS = {
  home: '&#xe6cc;', // shouye
  chat: '&#xe7de;', // huati
  generate: '&#xe82c;', // meishu
  matting: '&#xe7b4;', // caijian
  models: '&#xe8d3;', // xinpian
  assets: '&#xe6ee;', // tupian
  tasks: '&#xe6d9;', // jilu
  settings: '&#xe6d0;' // shezhi2
}

export const asyncRoutes: AppRouteRecord[] = [
  {
    // 创作
    path: '/creation',
    name: 'Creation',
    component: 'Home', // 布局容器（src/views/index/index.vue）
    meta: { title: '创作', icon: ICONS.generate },
    children: [
      {
        path: 'home',
        name: 'StudioHome',
        component: '/studio/home',
        meta: { title: '工作台', icon: ICONS.home, fixedTab: true, keepAlive: true }
      },
      {
        path: 'chat',
        name: 'StudioChat',
        component: '/studio/chat',
        meta: { title: '对话工作台', icon: ICONS.chat, keepAlive: true }
      },
      {
        path: 'generate',
        name: 'StudioGenerate',
        component: '/studio/generate',
        meta: { title: '生图', icon: ICONS.generate, keepAlive: true }
      },
      {
        path: 'matting',
        name: 'StudioMatting',
        component: '/studio/matting',
        meta: { title: '抠图工具箱', icon: ICONS.matting, keepAlive: true }
      }
    ]
  },
  {
    // 管理
    path: '/manage',
    name: 'Manage',
    component: 'Home',
    meta: { title: '管理', icon: ICONS.models },
    children: [
      {
        path: 'models',
        name: 'StudioModels',
        component: '/studio/models',
        meta: { title: '模型中心', icon: ICONS.models, keepAlive: true }
      },
      {
        path: 'assets',
        name: 'StudioAssets',
        component: '/studio/assets',
        meta: { title: '资产库', icon: ICONS.assets, keepAlive: true }
      },
      {
        path: 'tasks',
        name: 'StudioTasks',
        component: '/studio/tasks',
        meta: { title: '任务中心', icon: ICONS.tasks, keepAlive: true }
      },
      {
        path: 'help',
        name: 'StudioHelp',
        component: '/studio/help',
        meta: { title: '帮助中心', icon: '&#xe6b4;', keepAlive: true }
      }
    ]
  },
  {
    // 系统
    path: '/system',
    name: 'System',
    component: 'Home',
    meta: { title: '系统', icon: ICONS.settings },
    children: [
      {
        path: 'settings',
        name: 'StudioSettings',
        component: '/studio/settings',
        meta: { title: '系统设置', icon: ICONS.settings, keepAlive: true }
      }
    ]
  }
]

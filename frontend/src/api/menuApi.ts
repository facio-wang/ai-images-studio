import request from '@/utils/http'
import { BaseResponse } from '@/types/api'
import { AppRouteRecord } from '@/types/router'

interface MenuResponse {
  menuList: AppRouteRecord[]
}

// 菜单接口（Phase 1：从后端 /admin/menu/list 获取，按 admin.role_id 过滤）
export const menuService = {
  /**
   * 获取菜单列表
   * 后端控制模式下调用 /admin/menu/list，返回当前登录用户可见的菜单树
   * @returns { menuList } 菜单路由列表（已对齐 AppRouteRecord 类型）
   */
  async getMenuList(): Promise<MenuResponse> {
    try {
      const res = await request.get<BaseResponse<AppRouteRecord[]>>({
        url: '/admin/menu/list'
      })
      // 后端返回 { data, code, msg }，data 为菜单数组
      const menuList = res?.data ?? []
      return { menuList }
    } catch (error) {
      throw error instanceof Error ? error : new Error('获取菜单失败')
    }
  },

  /**
   * 获取完整菜单树（不过滤角色，供「角色分配菜单」树形选择器使用）
   * 后端返回树形结构数组，每项含 id/title/children 字段
   */
  async getAllMenus(): Promise<any[]> {
    const res = await request.get<BaseResponse<any[]>>({ url: '/admin/menu/all' })
    return res?.data ?? []
  }
}

import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

// 管理员列表项
export interface AdminItem {
  id: number
  username: string
  phone?: string
  email?: string
  gender?: number
  avatar?: string
  desc?: string
  role_id?: number
  role_name?: string
  role_title?: string
  status: number
  status_lable?: string
  create_time?: number | string
}

// 管理员新增/编辑参数
export interface AdminSaveParams {
  id?: number
  username: string
  password?: string
  phone?: string
  email?: string
  role_id?: number
  status?: number
  desc?: string
}

// 角色项
export interface RoleItem {
  id: number
  name: string
  title: string
  description?: string
  status: number
  menu_ids?: number[]
  menu_count?: number
}

// 管理员列表分页参数
export interface AdminListParams {
  page?: number
  size?: number
  phone?: string
  email?: string
  status?: number
}

export const AdminManageService = {
  // 管理员列表（后端返回 ThinkPHP Paginator：{ total, per_page, current_page, last_page, data, has_more }）
  getList(params?: AdminListParams) {
    return request.get<BaseResponse<any>>({ url: '/admin/admin/list', params })
  },
  // 新增/编辑（有 id 为编辑，无 id 为新增）
  save(data: AdminSaveParams) {
    return request.post<BaseResponse>({ url: '/admin/admin/save', data })
  },
  // 启用/禁用（后端翻转状态）
  toggle(id: number) {
    return request.post<BaseResponse>({ url: '/admin/admin/toggleStatus', data: { id } })
  },
  // 删除
  remove(id: number) {
    return request.del<BaseResponse>({ url: '/admin/admin/delete', data: { id } })
  }
}

export const RoleManageService = {
  // 角色列表（后端返回数组，非分页）
  getList() {
    return request.get<BaseResponse<RoleItem[]>>({ url: '/admin/role/list' })
  },
  // 新增
  save(data: Record<string, any>) {
    return request.post<BaseResponse>({ url: '/admin/role/save', data })
  },
  // 编辑
  update(data: Record<string, any>) {
    return request.put<BaseResponse>({ url: '/admin/role/update', data })
  },
  // 删除
  remove(id: number) {
    return request.del<BaseResponse>({ url: '/admin/role/delete', data: { id } })
  },
  // 分配菜单（全量覆盖）
  assignMenus(data: { id: number; menu_ids: number[] }) {
    return request.post<BaseResponse>({ url: '/admin/role/assignMenus', data })
  },
  // 获取角色已分配的菜单ID列表
  getMenus(id: number) {
    return request.get<BaseResponse<{ role_id: number; menu_ids: number[] }>>({
      url: '/admin/role/getMenus',
      params: { id }
    })
  }
}

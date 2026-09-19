import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

// APP用户（运营配置-用户列表, 2026-09-01）
export interface AppUserItem {
  id: number
  username: string
  nickname: string
  realname: string
  phone: string
  email: string
  gender: number
  age: number
  birthday: string | null
  img: string
  point: number
  level: number
  push_cid: string
  is_banned: number
  ban_reason: string
  banned_at_text: string
  ban_operator_id: number | null
  create_time_text: string
  update_time_text: string
}

export interface AppUserPermissions {
  roleId: number
  canBan: boolean
  canEdit: boolean
}

export interface AppUserListData {
  list: AppUserItem[]
  total: number
  page: number
  size: number
  permissions: AppUserPermissions
}

export interface AppUserDetailData {
  user: AppUserItem & { ban_operator_name: string }
  wechat: { open_id: string; nickname: string; phone: string; create_time_text: string } | null
  stats: {
    friend_count: number
    schedule_count: number
    goal_count: number
    chat_msg_count: number
    ai_chat_count: number
  }
  permissions: AppUserPermissions
}

export const AppUserService = {
  // 用户列表
  getList(params?: { page?: number; size?: number; keyword?: string; ban?: number | string }) {
    return request.get<BaseResponse<AppUserListData>>({ url: '/admin/app-user/list', params })
  },
  // 用户详情（全量数据）
  getDetail(id: number) {
    return request.get<BaseResponse<AppUserDetailData>>({ url: '/admin/app-user/detail', params: { id } })
  },
  // 封号（必须填写理由）
  ban(id: number, reason: string) {
    return request.post<BaseResponse>({ url: '/admin/app-user/ban', data: { id, reason } })
  },
  // 解除封号
  unban(id: number) {
    return request.post<BaseResponse>({ url: '/admin/app-user/unban', data: { id } })
  },
  // 编辑用户资料（仅超管）
  save(id: number, data: Partial<AppUserItem>) {
    return request.post<BaseResponse>({ url: '/admin/app-user/save', data: { id, ...data } })
  }
}

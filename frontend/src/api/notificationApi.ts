import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

// 推送列表项（后端返回 camelCase）
export interface NotificationItem {
  id: number
  title: string
  content: string
  type: string
  targetType: string
  targetUsers: number[]
  status: number
  sendType: string
  sendTime: number | null
  createTime: number | null
}

// 推送列表分页参数
export interface NotificationListParams {
  page?: number
  size?: number
  type?: string
  status?: number
  title?: string
}

// 推送列表响应数据
export interface NotificationListData {
  list: NotificationItem[]
  total: number
  page: number
  size: number
}

// 新建推送入参（后端接收 snake_case）
export interface NotificationSaveParams {
  title: string
  content: string
  type: string
  target_type: string
  target_users?: number[]
  send_type: string
}

// 发送结果
export interface NotificationSendResult {
  success: boolean
  message?: string
  delivered?: number
}

export const NotificationService = {
  // 推送列表
  // 2026-08-31: 后端路由组 notification → notification-push
  // (原前缀与mobile模块同名, 遮蔽了APP端 /mobile/notification/list, 导致通知中心被劫持)
  getList(params?: NotificationListParams) {
    return request.get<BaseResponse<NotificationListData>>({ url: '/admin/notification-push/list', params })
  },
  // 新建推送（草稿）
  save(data: NotificationSaveParams) {
    return request.post<BaseResponse<{ id: number }>>({ url: '/admin/notification-push/save', data })
  },
  // 发送推送（即时）
  send(id: number) {
    return request.post<BaseResponse<NotificationSendResult>>({ url: '/admin/notification-push/send', data: { id } })
  },
  // 删除推送
  remove(id: number) {
    return request.del<BaseResponse>({ url: '/admin/notification-push/delete', data: { id } })
  }
}

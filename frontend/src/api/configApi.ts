import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

// 单条配置项
export interface ConfigItem {
  key: string
  value: any
  remark?: string
  status: number
}

// 分组配置
export interface ConfigGroup {
  title: string
  items: ConfigItem[]
}

// 配置列表（分组返回）
export type ConfigListData = Record<string, ConfigGroup>

// 保存配置入参
export interface ConfigSaveItem {
  key: string
  value: any
}

export interface ConfigSaveParams {
  items: ConfigSaveItem[]
}

// 测试结果
export interface ConfigTestResult {
  success: boolean
  message?: string
  [key: string]: any
}

export const ConfigService = {
  // 配置列表（分组返回）
  getList() {
    return request.get<BaseResponse<ConfigListData>>({ url: '/admin/config/list' })
  },
  // 按分组获取
  getByGroup(group: string) {
    return request.get<BaseResponse<ConfigItem[]>>({ url: '/admin/config/getByGroup', params: { group } })
  },
  // 保存配置（按组保存）
  save(data: ConfigSaveParams) {
    return request.post<BaseResponse>({ url: '/admin/config/save', data })
  },
  // 测试短信发送
  testSms(phone: string) {
    return request.post<BaseResponse<ConfigTestResult>>({ url: '/admin/config/testSms', data: { phone } })
  },
  // 测试邮件发送
  testEmail(address: string) {
    return request.post<BaseResponse<ConfigTestResult>>({ url: '/admin/config/testEmail', data: { address } })
  },
  // 测试OBS连接
  testObs() {
    return request.post<BaseResponse<ConfigTestResult>>({ url: '/admin/config/testObs', data: {} })
  },

  // ==================== 服务商列表（AI模型配置/云储存配置，2026-08-30） ====================
  // 服务商配置列表 group=ai|storage
  providerList(group: 'ai' | 'storage') {
    return request.get<BaseResponse<ProviderItem[]>>({ url: '/admin/config/providerList', params: { group } })
  },
  // 保存（新增/更新）服务商配置
  providerSave(data: { group: string; code: string; value: Record<string, any>; remark?: string }) {
    return request.post<BaseResponse<{ key: string }>>({ url: '/admin/config/providerSave', data })
  },
  // 设置生效服务商（组内唯一生效）
  providerSetActive(data: { group: string; code?: string; key?: string }) {
    return request.post<BaseResponse>({ url: '/admin/config/providerSetActive', data })
  },
  // 删除服务商配置（生效中的不可删）
  providerDelete(data: { group: string; code?: string; key?: string }) {
    return request.post<BaseResponse>({ url: '/admin/config/providerDelete', data })
  },
  // 测试AI服务商（真实发一条最小补全请求）
  testAi(data: { group: string; key?: string; value?: Record<string, any> }) {
    return request.post<BaseResponse<ConfigTestResult>>({ url: '/admin/config/testAi', data })
  },
  // 测试云储存服务商连通性
  testStorage(data: { group: string; code: string; value?: Record<string, any> }) {
    return request.post<BaseResponse<ConfigTestResult>>({ url: '/admin/config/testStorage', data })
  }
}

// 服务商配置项（列表行）
export interface ProviderItem {
  key: string
  code: string
  name: string
  value: Record<string, any> | null
  status: number
  is_active: boolean
}

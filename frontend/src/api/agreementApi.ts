import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

// 协议数据（用户协议/隐私政策）
export interface AgreementData {
  type: string
  title: string
  content: string
  updated_at?: string
}

export const AgreementService = {
  // 协议详情 type=user|privacy
  detail(type: string) {
    return request.get<BaseResponse<AgreementData>>({
      url: '/admin/agreement/detail',
      params: { type }
    })
  },
  // 保存协议（内容整体覆盖）
  save(data: { type: string; title?: string; content: string }) {
    return request.post<BaseResponse>({ url: '/admin/agreement/save', data })
  }
}

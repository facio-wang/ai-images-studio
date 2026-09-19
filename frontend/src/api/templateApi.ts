import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

// AI 模板列表项（后端返回 camelCase）
export interface AiTemplateItem {
  id: number
  type: string
  name: string
  content: string
  fields: string[]
  isActive: number
  sort: number
  createdAt: string
  updatedAt: string
}

// AI 模板新增/编辑参数（后端接收 snake_case）
export interface AiTemplateSaveParams {
  id?: number
  type: string
  name: string
  content: string
  fields: string[]
  is_active: number
  sort: number
}

// AI 模板列表分页参数
export interface AiTemplateListParams {
  page?: number
  size?: number
  type?: string
}

// 列表响应数据
export interface AiTemplateListData {
  list: AiTemplateItem[]
  total: number
  pageSize: number
  currentPage: number
}

export const AiTemplateService = {
  // 模板分页列表（后端返回 { list, total, pageSize, currentPage }）
  getList(params?: AiTemplateListParams) {
    return request.get<BaseResponse<AiTemplateListData>>({ url: '/admin/template/list', params })
  },
  // 新增
  save(data: AiTemplateSaveParams) {
    return request.post<BaseResponse>({ url: '/admin/template/save', data })
  },
  // 编辑
  update(data: Partial<AiTemplateSaveParams> & { id: number }) {
    return request.put<BaseResponse>({ url: '/admin/template/update', data })
  },
  // 删除
  remove(id: number) {
    return request.del<BaseResponse>({ url: '/admin/template/delete', data: { id } })
  }
}

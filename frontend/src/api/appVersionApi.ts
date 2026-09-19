import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

// APP版本列表项
export interface AppVersionItem {
  id: number
  versionName: string
  versionCode: number
  platform: string
  downloadUrl: string
  updateDescription?: string
  isForceUpdate: number
  isPublished: number
  fileSize: number
  createdAt?: string
  updatedAt?: string
}

// 列表分页参数
export interface AppVersionListParams {
  page?: number
  size?: number
  platform?: string
}

// 列表分页响应
export interface AppVersionListData {
  list: AppVersionItem[]
  total: number
  pageSize: number
  currentPage: number
}

// 新增/编辑表单数据(文件上传用 FormData)
export interface AppVersionFormData {
  id?: number
  version_name: string
  version_code: number
  platform: string
  download_url?: string
  update_description?: string
  is_force_update: number
  is_published?: number
  file_size?: number
}

export const AppVersionService = {
  // 版本列表
  getList(params?: AppVersionListParams) {
    return request.get<BaseResponse<AppVersionListData>>({
      url: '/admin/app-version/list',
      params
    })
  },
  // 新增版本（data 为 FormData，含可选 file 字段）
  save(data: FormData) {
    return request.post<BaseResponse>({
      url: '/admin/app-version/save',
      data,
      requestOptions: { disableJson: true }
    })
  },
  // 更新版本（data 为 FormData，含可选 file 字段用于替换包）
  update(data: FormData) {
    return request.put<BaseResponse>({
      url: '/admin/app-version/update',
      data,
      requestOptions: { disableJson: true }
    })
  },
  // 独立上传APK包（2026-09-03）: 先传包拿url, 再走save/update落库, 避免大包随表单提交超时
  uploadApk(data: FormData, onProgress?: (percent: number) => void) {
    return request.post<BaseResponse<{ url: string; fileSize: number }>>({
      url: '/admin/app-version/upload',
      data,
      onUploadProgress: (e: any) => {
        if (onProgress && e?.total) onProgress(Math.round((e.loaded / e.total) * 100))
      },
      requestOptions: { disableJson: true }
    })
  },
  // 删除版本（同步删OBS包）
  remove(id: number) {
    return request.del<BaseResponse>({ url: '/admin/app-version/delete', data: { id } })
  },
  // 发布版本
  publish(id: number) {
    return request.post<BaseResponse>({ url: '/admin/app-version/publish', data: { id } })
  },
  // 取消发布
  unpublish(id: number) {
    return request.post<BaseResponse>({ url: '/admin/app-version/unpublish', data: { id } })
  }
}

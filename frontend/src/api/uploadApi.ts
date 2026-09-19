import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

export class uploadService {
  // 上传
  static upload(params: FormData) {
    return request.post<BaseResponse>({
      url: '/admin/upload/image',
      data: params,
      // 添加自定义请求选项
      requestOptions: {
        // 禁用自动 JSON 转换
        disableJson: true
      }
    })
  }
}

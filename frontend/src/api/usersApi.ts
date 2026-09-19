import request from '@/utils/http'
import { BaseResponse } from '@/types/api'

interface LoginParams {
  username: string
  password: string
}

interface UserListParams {
  page?: number
  size?: number
}

interface UserItemParams {
  id: string
  username: string
  phone: string
  gender: number
  role: string[]
}

interface UserInfoParams {
  isPwd: boolean
  username?: string
  phone?: string
  email?: string
  gender?: number
  avatar?: string
  desc?: string
  password?: string
  newPassword?: string
  confirmPassword?: string
}

// 飞书绑定状态
interface FeishuBindStatus {
  platform: string
  is_bound: boolean
  nickname: string
  avatar: string
}

export class UserService {
  // 登录
  static login(params: LoginParams) {
    return request.post<BaseResponse>({
      url: '/admin/login/login',
      params
    })
  }

  // 获取用户信息
  static getUserInfo() {
    return request.get<BaseResponse>({
      url: '/admin/admin/info'
    })
  }

  // 获取用户列表
  static getUserList(params?: UserListParams) {
    return request.get<BaseResponse>({
      url: '/admin/admin/list',
      params
    })
  }

  // 编辑用户信息
  static saveUser(params?: UserItemParams) {
    return request.post<BaseResponse>({
      url: '/admin/admin/save',
      data: params
    })
  }

  // 编辑个人信息
  static saveUserInfo(params?: UserInfoParams) {
    return request.post<BaseResponse>({
      url: '/admin/admin/saveInfo',
      data: params
    })
  }

  // 退出登录
  static logout() {
    return request.post<BaseResponse>({
      url: '/admin/login/logout'
    })
  }

  // 获取飞书登录授权URL（公开）
  static getFeishuAuthUrl() {
    return request.get<BaseResponse<{ url: string }>>({
      url: '/admin/login/feishuAuthUrl'
    })
  }

  // 获取飞书绑定授权URL（需登录）
  static getFeishuBindAuthUrl() {
    return request.get<BaseResponse<{ url: string }>>({
      url: '/admin/login/feishuBindAuthUrl'
    })
  }

  // 查询飞书绑定状态（需登录）
  static getFeishuBindStatus() {
    return request.get<BaseResponse<FeishuBindStatus>>({
      url: '/admin/login/feishuBindStatus'
    })
  }

  // 解绑飞书账号（需登录）
  static feishuUnbind() {
    return request.post<BaseResponse>({
      url: '/admin/login/feishuUnbind'
    })
  }
}
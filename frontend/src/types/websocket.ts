// WebSocket相关类型定义

// WebSocket连接状态枚举
export enum WebSocketStatus {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  ERROR = 'ERROR'
}

// 扫码登录状态枚举
export enum QrCodeLoginStatus {
  WAITING = 'waiting',      // 等待扫描
  SCANNED = 'scanned',      // 已扫描
  CONFIRMED = 'confirmed',   // 已确认
  CANCELLED = 'cancelled',   // 已取消
  EXPIRED = 'expired'       // 已过期
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: string
  data?: any
}

// 扫码登录状态变化回调函数
export type QrCodeStatusCallback = (status: QrCodeLoginStatus, data?: any) => void
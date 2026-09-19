<template>
  <div class="qrcode-container" :style="{ width: `${size}px`, height: `${size}px` }">
    <!-- 加载状态 -->
    <div v-if="loading" class="status-container loading">
      <img :src="loadingImg" alt="加载中" class="status-image" :style="imageStyle" />
      <p class="loading-text">加载中...</p>
    </div>

    <!-- 二维码显示区域 -->
    <div class="qrcode-wrapper" v-show="!loading" @click="handleRefresh">
      <qrcode-vue
          ref="qrcode"
          :value="config.value"
          :size="size"
          :level="config.level"
          :renderAs="config.renderAs"
          :margin="config.margin"
          :background="config.background"
          :foreground="config.foreground"
          :imageSettings="config.imageSettings"
          class="qrcode-image"
      />

      <!-- 过期状态遮罩 -->
      <div v-if="expired || autoExpired"
           class="expired-overlay"
           @click.stop="handleRefresh"
        >
        <div class="refresh-content">
          <i class="iconfont-sys" style="font-size: 40px" :style="{pointerEvents: 'none'}">&#xe6b3;</i>
          <p class="refresh-text" :style="{pointerEvents: 'none'}">刷新</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import QrcodeVue from 'qrcode.vue'
import type { Level, RenderAs, ImageSettings } from 'qrcode.vue'

import loadingImg from '@/assets/img/common/ikun-logo.png'

// 组件属性定义
const props = defineProps({
  // 二维码配置
  config: {
    type: Object,
    required: true,
    default: () => ({
      value: 'https://www.example.com',
      size: 200,
      level: 'H' as Level,
      renderAs: 'canvas' as RenderAs,
      margin: 2,
      background: '#ffffff',
      foreground: '#000000',
      imageSettings: null as ImageSettings | null
    })
  },
  // 图片大小
  size: {
    type: Number,
    default: 200
  },
  // 是否过期
  expired: {
    type: Boolean,
    default: false
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

// 自动过期状态
const autoExpired = ref(false)

// 计时器
const refreshTimer = ref<NodeJS.Timeout | null>(null)
const timeLeft = ref(300) // 5分钟（300秒）
const maxTime = 300 // 最大时间（秒）

// 计算图片样式
const imageStyle = computed(() => {
  const imgSize = Math.max(40, props.size * 0.3)
  return {
    width: `${imgSize}px`,
    height: `${imgSize}px`
  }
})

const emit = defineEmits(['refresh'])

// 初始加载状态
const initialLoading = ref(true)
onMounted(() => {
  setTimeout(() => {
    initialLoading.value = false
  }, 400)
  startRefreshTimer()
})

// 监听过期状态变化
watch(() => props.expired, (newVal) => {
  if (newVal) {
    // 如果父组件设置过期，停止计时器
    stopRefreshTimer()
  } else {
    // 如果父组件取消过期，重新开始计时
    startRefreshTimer()
  }
})

// 组件卸载时清理
onUnmounted(() => {
  stopRefreshTimer()
})

// 开始刷新计时器
function startRefreshTimer() {
  // 重置状态和时间
  autoExpired.value = false
  timeLeft.value = maxTime

  // 清除现有计时器
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }

  // 创建新的计时器
  refreshTimer.value = setInterval(() => {
    timeLeft.value -= 1

    // 检查是否超过最大时间
    if (timeLeft.value <= 0) {
      autoExpired.value = true
      stopRefreshTimer()
    }
  }, 1000)
}

// 停止刷新计时器
function stopRefreshTimer() {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 处理刷新操作
function handleRefresh() {
  // 重置自动过期状态
  autoExpired.value = false

  // 通知父组件刷新
  emit('refresh')

  // 重新开始计时
  startRefreshTimer()
}
</script>

<style scoped>
.qrcode-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s ease;
}

.qrcode-container:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.qrcode-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.qrcode-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background-color: white;
  padding: 8px;
  border-radius: 6px;
}

/* 加载状态样式 */
.status-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.status-image {
  display: block;
  animation: spin 1.5s linear infinite;
}

.loading-text {
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

/* 过期状态样式 */
.expired-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  border-radius: 6px;
  backdrop-filter: blur(2px);
  cursor: pointer;
}

.refresh-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
}
.refresh-text{
  margin-top: 10px;
}

/* 动画 */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
</style>
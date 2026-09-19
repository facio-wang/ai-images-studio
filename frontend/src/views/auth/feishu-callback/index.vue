<template>
  <div class="feishu-callback">
    <div class="callback-box art-custom-card">
      <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
      <el-icon v-else-if="errorMsg" class="error-icon"><CircleCloseFilled /></el-icon>
      <el-icon v-else class="success-icon"><CircleCheckFilled /></el-icon>
      <p class="callback-text">{{ statusText }}</p>
      <p v-if="errorMsg" class="callback-error">{{ errorMsg }}</p>
      <el-button v-if="errorMsg" type="primary" @click="goLogin">返回登录</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import { Loading, CircleCloseFilled, CircleCheckFilled } from '@element-plus/icons-vue'
  import { useUserStore } from '@/store/modules/user'
  import { UserService } from '@/api/usersApi'
  import { ApiStatus } from '@/utils/http/status'
  import { RoutesAlias, HOME_PAGE } from '@/router/routesAlias'

  const router = useRouter()
  const route = useRoute()
  const userStore = useUserStore()

  const loading = ref(true)
  const errorMsg = ref('')
  const statusText = ref('飞书登录处理中...')

  const goLogin = () => {
    router.replace(RoutesAlias.Login)
  }

  const handleCallback = async () => {
    const token = (route.query.token as string) || ''
    const error = (route.query.error as string) || ''

    if (error) {
      loading.value = false
      errorMsg.value = error
      statusText.value = '飞书登录失败'
      return
    }

    if (!token) {
      loading.value = false
      errorMsg.value = '未获取到登录凭证'
      statusText.value = '飞书登录失败'
      return
    }

    try {
      // 保存 token 并拉取用户信息
      userStore.setToken(token)
      userStore.setLoginStatus(true)
      const res = await UserService.getUserInfo()
      if (res.code === ApiStatus.success) {
        userStore.setUserInfo(res.data)
      }
      statusText.value = '登录成功，正在跳转...'
      loading.value = false
      ElMessage.success('飞书登录成功')
      setTimeout(() => {
        router.replace(HOME_PAGE)
      }, 600)
    } catch (e: any) {
      loading.value = false
      errorMsg.value = e?.message || '登录信息获取失败'
      statusText.value = '飞书登录失败'
    }
  }

  onMounted(() => {
    handleCallback()
  })
</script>

<style lang="scss" scoped>
  .feishu-callback {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: var(--art-main-bg-color);

    .callback-box {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 40px 48px;
      border-radius: 12px;
      gap: 16px;
      min-width: 320px;
      text-align: center;

      .el-icon {
        font-size: 48px;

        &.is-loading {
          color: var(--el-color-primary);
        }
      }

      .error-icon {
        color: var(--el-color-danger);
      }

      .success-icon {
        color: var(--el-color-success);
      }

      .callback-text {
        font-size: 16px;
        font-weight: 500;
        margin: 0;
      }

      .callback-error {
        font-size: 13px;
        color: var(--el-text-color-secondary);
        margin: 0;
        word-break: break-all;
      }
    }
  }
</style>

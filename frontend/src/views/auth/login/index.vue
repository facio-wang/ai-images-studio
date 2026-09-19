<!-- 登录页：单字段 Token 登录（AI Images Studio 后端 Bearer 鉴权） -->
<template>
  <div class="login">
    <LoginLeftView></LoginLeftView>

    <div class="right-wrap">
      <div class="top-right-wrap">
        <div class="btn theme-btn" @click="toggleTheme">
          <i class="iconfont-sys">
            {{ isDark ? '&#xe6b5;' : '&#xe725;' }}
          </i>
        </div>
      </div>
      <div class="header">
        <div class="studio-logo">AI</div>
        <h1>AI Images Studio</h1>
      </div>
      <div class="login-wrap">
        <div class="form">
          <h3 class="title">登录工作台</h3>
          <p class="sub-title">请输入访问令牌（Token）以进入创作中台 · 仅限局域网授权用户</p>
          <ElForm
            ref="formRef"
            :model="formData"
            :rules="rules"
            @keyup.enter="handleSubmit"
            style="margin-top: 25px"
          >
            <ElFormItem prop="token">
              <ElInput
                v-model.trim="formData.token"
                type="password"
                show-password
                placeholder="请输入访问令牌（服务端 .env 中的 STUDIO_TOKEN）"
                radius="8px"
                autocomplete="off"
              />
            </ElFormItem>

            <div style="margin-top: 30px">
              <ElButton class="login-btn" type="primary" @click="handleSubmit" :loading="loading" v-ripple>
                登录工作台 →
              </ElButton>
            </div>

            <div class="login-footer">
              <span>Token 配置于服务端 .env 的 STUDIO_TOKEN</span>
              <span>本地会话 · 令牌仅存于浏览器 localStorage</span>
            </div>
          </ElForm>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElNotification } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import { HOME_PAGE } from '@/router/routesAlias'
import type { FormInstance, FormRules } from 'element-plus'
import { verifyToken } from '@/api/studio'

defineOptions({ name: 'Login' })

const formRef = ref<FormInstance>()
const userStore = useUserStore()
const router = useRouter()
const loading = ref(false)

const formData = reactive({ token: '' })

const rules = computed<FormRules>(() => ({
  token: [{ required: true, message: '请输入访问令牌', trigger: 'blur' }]
}))

/** 提交：校验 token（调受保护接口 200 即有效）→ 写入 store → 进工作台 */
const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const ok = await verifyToken(formData.token)
      if (!ok) {
        ElMessage.error('令牌无效或服务不可达，请检查后重试')
        return
      }
      // 写入 token 并标记登录态；角色固定（单用户）
      userStore.setToken(formData.token)
      userStore.setUserInfo({ userId: 1, username: 'Studio User', roles: ['admin'], buttons: [] })
      userStore.setLoginStatus(true)
      showLoginSuccessNotice()
      await router.push(HOME_PAGE)
    } finally {
      loading.value = false
    }
  })
}

// 登录成功提示
const showLoginSuccessNotice = () => {
  setTimeout(() => {
    ElNotification({
      type: 'success',
      title: '登录成功',
      message: '欢迎回到 AI Images Studio!',
      zIndex: 10000
    })
  }, 150)
}

// 切换主题
import { useTheme } from '@/composables/useTheme'
import { useSettingStore } from '@/store/modules/setting'
import { storeToRefs } from 'pinia'
import { SystemThemeEnum } from '@/enums/appEnum'

const settingStore = useSettingStore()
const { isDark, systemThemeType } = storeToRefs(settingStore)

const toggleTheme = () => {
  let { LIGHT, DARK } = SystemThemeEnum
  useTheme().switchThemeStyles(systemThemeType.value === LIGHT ? DARK : LIGHT)
}
</script>

<style lang="scss" scoped>
  @use './index';

  .header {
    display: flex;
    align-items: center;
    gap: 12px;

    .studio-logo {
      width: 42px;
      height: 42px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: 800;
      color: #fff;
      border-radius: 6px;
      background: linear-gradient(135deg, #2563eb, #06b6d4);
    }
  }

  .login-footer {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: 22px;
    padding-top: 14px;
    border-top: 1px solid var(--art-border-dashed-color);
    font-size: 11px;
    color: var(--art-gray-500);
  }
</style>

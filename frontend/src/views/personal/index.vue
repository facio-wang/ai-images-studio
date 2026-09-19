<template>
  <div class="personal-center page-container">
    <!-- 顶部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">个人中心</h2>
        <p class="page-desc">查看个人信息与修改登录密码</p>
      </div>
      <div class="header-right">
        <el-button :icon="Refresh" @click="fetchUserInfo">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 基本信息卡片 -->
      <el-col :xs="24" :sm="24" :md="10" :lg="8" :xl="8">
        <div class="info-card art-custom-card" v-loading="loading">
          <div v-loading="uploadingAvatar" class="avatar-box">
            <el-avatar :size="90" :src="userInfo.avatar">
              {{ userInfo.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <!-- 头像上传蒙层 -->
            <div class="avatar-mask" title="更换头像" @click="triggerAvatarUpload">
              <el-icon><Camera /></el-icon>
              <span>更换</span>
            </div>
            <input
              ref="avatarInputRef"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              style="display: none"
              @change="onAvatarFileChange"
            />
          </div>
          <h3 class="user-name">{{ userInfo.username || '-' }}</h3>
          <p class="user-role">
            <el-tag size="small" type="primary">{{ roleText }}</el-tag>
          </p>
          <ul class="info-list">
            <li>
              <span class="label">手机号</span>
              <span class="value">{{ userInfo.phone || '-' }}</span>
            </li>
            <li>
              <span class="label">邮箱</span>
              <span class="value">{{ userInfo.email || '-' }}</span>
            </li>
            <li>
              <span class="label">用户ID</span>
              <span class="value">{{ userInfo.userId || '-' }}</span>
            </li>
            <li>
              <span class="label">简介</span>
              <span class="value">{{ userInfo.desc || '-' }}</span>
            </li>
          </ul>
          <el-button type="primary" plain class="edit-btn" :icon="EditPen" @click="openEditDialog">编辑资料</el-button>
        </div>
      </el-col>

      <!-- 修改密码卡片 -->
      <el-col :xs="24" :sm="24" :md="14" :lg="16" :xl="16">
        <div class="pwd-card art-custom-card">
          <h3 class="card-title">修改密码</h3>
          <p class="card-desc">修改登录密码后需重新登录，请牢记新密码</p>
          <el-form
            ref="pwdFormRef"
            :model="pwdForm"
            :rules="pwdRules"
            label-width="100px"
            class="pwd-form"
            @submit.prevent="onSubmitPwd"
          >
            <el-form-item label="原密码" prop="password">
              <el-input
                v-model="pwdForm.password"
                type="password"
                placeholder="请输入当前密码"
                show-password
                clearable
              />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input
                v-model="pwdForm.newPassword"
                type="password"
                placeholder="请输入新密码（至少6位）"
                show-password
                clearable
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="pwdForm.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password
                clearable
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="onSubmitPwd">确认修改</el-button>
              <el-button @click="onResetPwd">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>

    <!-- 第三方账号绑定 -->
    <el-row :gutter="16" class="oauth-row">
      <el-col :span="24">
        <div class="oauth-card art-custom-card">
          <h3 class="card-title">第三方账号绑定</h3>
          <p class="card-desc">绑定后可使用对应平台扫码登录本系统</p>
          <div class="oauth-item" v-loading="oauthLoading">
            <div class="oauth-info">
              <img :src="feishuLogo" alt="feishu" class="oauth-logo" />
              <div class="oauth-text">
                <span class="oauth-name">飞书</span>
                <template v-if="feishuBound">
                  <span class="oauth-bound">
                    已绑定：{{ feishuStatus.nickname || '飞书用户' }}
                  </span>
                </template>
                <span v-else class="oauth-unbound">未绑定</span>
              </div>
            </div>
            <div class="oauth-action">
              <el-button v-if="!feishuBound" type="primary" plain :loading="binding" @click="handleFeishuBind">
                绑定飞书
              </el-button>
              <template v-else>
                <el-button type="danger" plain :loading="unbinding" @click="handleFeishuUnbind">
                  解绑
                </el-button>
              </template>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 编辑资料弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑个人资料" width="480px" destroy-on-close>
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" placeholder="用户名" maxlength="30" clearable />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" placeholder="手机号" maxlength="11" clearable />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="邮箱地址" clearable />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="editForm.gender">
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
            <el-radio :value="0">保密</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="editForm.desc" type="textarea" :rows="3" placeholder="一句话介绍自己（可选）" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingProfile" @click="onSubmitProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, computed, onMounted } from 'vue'
  import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
  import { Refresh, EditPen, Camera } from '@element-plus/icons-vue'
  import { useUserStore } from '@/store/modules/user'
  import { UserService } from '@/api/usersApi'
  import { uploadService } from '@/api/uploadApi'
  import { ApiStatus } from '@/utils/http/status'
  import feishuLogo from '@/assets/img/logo/feishu-logo.svg'

  const userStore = useUserStore()
  const loading = ref(false)
  const saving = ref(false)
  const pwdFormRef = ref<FormInstance>()

  // 用户信息（优先用 store 缓存，再拉接口刷新）
  const userInfo = reactive({
    userId: 0,
    username: '',
    avatar: '',
    phone: '',
    email: '',
    gender: 0,
    desc: '',
    roles: [] as string[]
  })

  const roleText = computed(() => {
    const roles = userInfo.roles || []
    if (roles.includes('R_SUPER')) return '超级管理员'
    if (roles.includes('R_ADMIN')) return '管理员'
    return '普通用户'
  })

  // 修改密码表单
  const pwdForm = reactive({
    password: '',
    newPassword: '',
    confirmPassword: ''
  })

  const pwdRules: FormRules = {
    password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
    newPassword: [
      { required: true, message: '请输入新密码', trigger: 'blur' },
      { min: 6, message: '密码至少6位', trigger: 'blur' }
    ],
    confirmPassword: [
      { required: true, message: '请再次输入新密码', trigger: 'blur' },
      {
        validator: (_rule, value, callback) => {
          if (value !== pwdForm.newPassword) {
            callback(new Error('两次输入的密码不一致'))
          } else {
            callback()
          }
        },
        trigger: 'blur'
      }
    ]
  }

  // 拉取用户信息
  const fetchUserInfo = async () => {
    loading.value = true
    try {
      const res = await UserService.getUserInfo()
      const data = res?.data || {}
      userInfo.userId = data.userId || 0
      userInfo.username = data.username || ''
      userInfo.avatar = data.avatar || ''
      userInfo.phone = data.phone || ''
      userInfo.email = data.email || ''
      userInfo.gender = data.gender ?? 0
      userInfo.desc = data.desc || ''
      userInfo.roles = data.roles || []
      // 同步更新 store 缓存
      if (userStore.getUserInfo) {
        userStore.setUserInfo({ ...userStore.getUserInfo, ...data })
      }
    } catch (e: any) {
      ElMessage.error(e?.message || '获取用户信息失败')
    } finally {
      loading.value = false
    }
  }

  // 提交修改密码
  const onSubmitPwd = async () => {
    if (!pwdFormRef.value) return
    await pwdFormRef.value.validate(async (valid) => {
      if (!valid) return
      saving.value = true
      try {
        await UserService.saveUserInfo({
          isPwd: true,
          password: pwdForm.password,
          newPassword: pwdForm.newPassword,
          confirmPassword: pwdForm.confirmPassword
        })
        ElMessage.success('密码修改成功，请重新登录')
        // 修改密码后强制重新登录
        setTimeout(() => {
          userStore.logOut()
        }, 1500)
      } catch (e: any) {
        ElMessage.error(e?.message || '修改失败，请重试')
      } finally {
        saving.value = false
      }
    })
  }

  const onResetPwd = () => {
    pwdFormRef.value?.resetFields()
  }

  // ==================== 编辑资料 ====================
  const editDialogVisible = ref(false)
  const savingProfile = ref(false)
  const editFormRef = ref<FormInstance>()
  const editForm = reactive({
    username: '',
    phone: '',
    email: '',
    gender: 0,
    desc: ''
  })

  const editRules: FormRules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    phone: [
      { required: true, message: '请输入手机号', trigger: 'blur' },
      { pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }
    ],
    email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }]
  }

  const openEditDialog = () => {
    Object.assign(editForm, {
      username: userInfo.username || '',
      phone: userInfo.phone || '',
      email: userInfo.email || '',
      gender: userInfo.gender ?? 0,
      desc: userInfo.desc || ''
    })
    editDialogVisible.value = true
  }

  const onSubmitProfile = async () => {
    if (!editFormRef.value) return
    await editFormRef.value.validate(async (valid) => {
      if (!valid) return
      savingProfile.value = true
      try {
        await UserService.saveUserInfo({
          isPwd: false,
          username: editForm.username,
          phone: editForm.phone,
          email: editForm.email,
          gender: editForm.gender,
          desc: editForm.desc
        })
        ElMessage.success('资料保存成功')
        editDialogVisible.value = false
        await fetchUserInfo()
      } catch (e: any) {
        ElMessage.error(e?.message || '保存失败，请重试')
      } finally {
        savingProfile.value = false
      }
    })
  }

  // ==================== 头像上传 ====================
  const avatarInputRef = ref<HTMLInputElement>()
  const uploadingAvatar = ref(false)

  const triggerAvatarUpload = () => {
    avatarInputRef.value?.click()
  }

  const onAvatarFileChange = async (event: Event) => {
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    // 重置 value 允许连续选择同一文件
    input.value = ''
    if (!file) return
    if (file.size > 5 * 1024 * 1024) {
      ElMessage.warning('头像图片不能超过5M')
      return
    }
    uploadingAvatar.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('scene', 'avatar')
      const res = await uploadService.upload(formData)
      const url = res?.data?.url || res?.data?.base_url
      if (!url) {
        ElMessage.error('上传失败：未返回图片地址')
        return
      }
      // 上传成功后写入 avatar 字段
      await UserService.saveUserInfo({ isPwd: false, avatar: url })
      userInfo.avatar = url
      if (userStore.getUserInfo) {
        userStore.setUserInfo({ ...userStore.getUserInfo, avatar: url } as any)
      }
      ElMessage.success('头像更新成功')
    } catch (e: any) {
      ElMessage.error(e?.message || '头像上传失败')
    } finally {
      uploadingAvatar.value = false
    }
  }

  // ==================== 第三方账号绑定（飞书） ====================
  const oauthLoading = ref(false)
  const binding = ref(false)
  const unbinding = ref(false)
  const feishuStatus = reactive({
    is_bound: false,
    nickname: '',
    avatar: ''
  })
  const feishuBound = computed(() => feishuStatus.is_bound)

  // 拉取飞书绑定状态
  const fetchFeishuStatus = async () => {
    oauthLoading.value = true
    try {
      const res = await UserService.getFeishuBindStatus()
      const data = res?.data || {}
      feishuStatus.is_bound = !!data.is_bound
      feishuStatus.nickname = data.nickname || ''
      feishuStatus.avatar = data.avatar || ''
    } catch (e: any) {
      // 静默失败，不影响页面其他功能
      console.error('获取飞书绑定状态失败:', e)
    } finally {
      oauthLoading.value = false
    }
  }

  // 绑定飞书：获取授权URL后跳转，回调由后端重定向回个人中心
  const handleFeishuBind = async () => {
    binding.value = true
    try {
      const res = await UserService.getFeishuBindAuthUrl()
      if (res.code === ApiStatus.success && res.data?.url) {
        window.location.href = res.data.url
      } else {
        ElMessage.error(res.msg || '获取飞书授权地址失败')
      }
    } catch (e: any) {
      ElMessage.error(e?.message || '获取飞书授权地址失败')
    } finally {
      binding.value = false
    }
  }

  // 解绑飞书
  const handleFeishuUnbind = async () => {
    try {
      await ElMessageBox.confirm('解绑后将无法使用飞书扫码登录，确认解绑？', '解绑飞书', {
        type: 'warning',
        confirmButtonText: '确认解绑',
        cancelButtonText: '取消'
      })
    } catch {
      return
    }
    unbinding.value = true
    try {
      const res = await UserService.feishuUnbind()
      if (res.code === ApiStatus.success) {
        ElMessage.success('已解绑飞书账号')
        feishuStatus.is_bound = false
        feishuStatus.nickname = ''
        feishuStatus.avatar = ''
      } else {
        ElMessage.error(res.msg || '解绑失败')
      }
    } catch (e: any) {
      ElMessage.error(e?.message || '解绑失败')
    } finally {
      unbinding.value = false
    }
  }

  // 绑定回调回来后，个人中心URL可能带 error 参数，提示一下
  const checkBindResult = () => {
    const params = new URLSearchParams(window.location.search)
    const err = params.get('error')
    if (err) {
      ElMessage.error(decodeURIComponent(err))
      // 清理URL参数
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (params.get('token') === null && params.has('token') === false) {
      // 无 error 也无 token：可能是绑定成功跳回，刷新状态
    }
  }

  onMounted(() => {
    // 先用 store 缓存快速填充
    const cached = userStore.getUserInfo
    if (cached) {
      userInfo.userId = cached.userId || 0
      userInfo.username = cached.username || ''
      userInfo.avatar = cached.avatar || ''
      userInfo.phone = cached.phone || ''
      userInfo.email = cached.email || ''
      userInfo.desc = cached.desc || ''
      userInfo.roles = cached.roles || []
    }
    fetchUserInfo()
    fetchFeishuStatus()
    checkBindResult()
  })
</script>

<style lang="scss" scoped>
  .personal-center {
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      .page-title {
        font-size: 20px;
        font-weight: 600;
        margin: 0 0 4px;
      }

      .page-desc {
        font-size: 13px;
        color: var(--el-text-color-secondary);
        margin: 0;
      }
    }

    .info-card {
      padding: 24px;
      text-align: center;
      border-radius: var(--custom-radius, 8px);

      .avatar-box {
        margin-bottom: 12px;
        position: relative;
        display: inline-block;

        .avatar-mask {
          position: absolute;
          left: 50%;
          top: 0;
          transform: translateX(-50%);
          width: 90px;
          height: 90px;
          border-radius: 50%;
          background: rgba(0, 0, 0, 0.45);
          color: #fff;
          display: none;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          font-size: 12px;
          gap: 2px;

          .el-icon {
            font-size: 18px;
          }
        }

        &:hover .avatar-mask {
          display: flex;
        }
      }

      .edit-btn {
        margin-top: 12px;
      }

      .user-name {
        font-size: 18px;
        font-weight: 600;
        margin: 0 0 8px;
      }

      .user-role {
        margin: 0 0 20px;
      }

      .info-list {
        list-style: none;
        padding: 0;
        margin: 0;
        text-align: left;

        li {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 0;
          border-bottom: 1px solid var(--el-border-color-lighter);
          font-size: 14px;

          &:last-child {
            border-bottom: none;
          }

          .label {
            color: var(--el-text-color-secondary);
          }

          .value {
            color: var(--el-text-color-primary);
            font-weight: 500;
            max-width: 60%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }
      }
    }

    .pwd-card {
      padding: 24px;
      border-radius: var(--custom-radius, 8px);

      .card-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 4px;
      }

      .card-desc {
        font-size: 13px;
        color: var(--el-text-color-secondary);
        margin: 0 0 20px;
      }

      .pwd-form {
        max-width: 460px;
      }
    }

    .oauth-row {
      margin-top: 16px;
    }

    .oauth-card {
      padding: 24px;
      border-radius: var(--custom-radius, 8px);

      .card-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 4px;
      }

      .card-desc {
        font-size: 13px;
        color: var(--el-text-color-secondary);
        margin: 0 0 20px;
      }

      .oauth-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        border-top: 1px solid var(--el-border-color-lighter);

        .oauth-info {
          display: flex;
          align-items: center;
          gap: 12px;

          .oauth-logo {
            width: 32px;
            height: 32px;
            border-radius: 6px;
          }

          .oauth-text {
            display: flex;
            flex-direction: column;
            gap: 4px;

            .oauth-name {
              font-size: 14px;
              font-weight: 500;
              color: var(--el-text-color-primary);
            }

            .oauth-bound {
              font-size: 12px;
              color: var(--el-color-success);
            }

            .oauth-unbound {
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }
        }
      }
    }
  }
</style>

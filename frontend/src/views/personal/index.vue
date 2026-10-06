<!-- 个人中心：本地头像上传 + 资料编辑（单用户 Token 登录，无密码/三方绑定） -->
<template>
  <div class="personal-center page-container">
    <!-- 顶部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">{{ $t('studio.personal.title') }}</h2>
        <p class="page-desc">{{ $t('studio.personal.desc') }}</p>
      </div>
      <div class="header-right">
        <el-button :icon="Refresh" @click="refreshFromStore">{{ $t('studio.personal.refresh') }}</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 基本信息卡片 -->
      <el-col :xs="24" :sm="24" :md="10" :lg="8" :xl="8">
        <div class="info-card art-custom-card">
          <div class="avatar-box">
            <el-avatar :size="90" :src="userInfo.avatar">
              {{ (userInfo.username || 'S').charAt(0).toUpperCase() }}
            </el-avatar>
            <!-- 头像上传蒙层 -->
            <div class="avatar-mask" :title="$t('studio.personal.changeAvatar')" @click="triggerAvatarUpload">
              <el-icon><Camera /></el-icon>
              <span>{{ $t('studio.personal.change') }}</span>
            </div>
            <input
              ref="avatarInputRef"
              type="file"
              accept="image/png,image/jpeg,image/webp"
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
              <span class="label">{{ $t('studio.personal.phone') }}</span>
              <span class="value">{{ userInfo.phone || '-' }}</span>
            </li>
            <li>
              <span class="label">{{ $t('studio.personal.email') }}</span>
              <span class="value">{{ userInfo.email || '-' }}</span>
            </li>
            <li>
              <span class="label">{{ $t('studio.personal.userId') }}</span>
              <span class="value">{{ userInfo.userId || '-' }}</span>
            </li>
            <li>
              <span class="label">{{ $t('studio.personal.bio') }}</span>
              <span class="value">{{ userInfo.desc || '-' }}</span>
            </li>
          </ul>
          <el-button type="primary" plain class="edit-btn" :icon="EditPen" @click="openEditDialog">
            {{ $t('studio.personal.editProfile') }}
          </el-button>
        </div>
      </el-col>

      <!-- 账号与登录说明（单用户 Token 登录：无密码编辑、无三方绑定） -->
      <el-col :xs="24" :sm="24" :md="14" :lg="16" :xl="16">
        <div class="account-card art-custom-card">
          <h3 class="card-title">{{ $t('studio.personal.accountCard') }}</h3>
          <p class="card-desc">{{ $t('studio.personal.accountIntro') }}</p>
          <ul class="account-list">
            <li>
              <el-icon><Key /></el-icon>
              <span>{{ $t('studio.personal.accountTip1') }}</span>
            </li>
            <li>
              <el-icon><Lock /></el-icon>
              <span>{{ $t('studio.personal.accountTip2') }}</span>
            </li>
            <li>
              <el-icon><Refresh /></el-icon>
              <span>{{ $t('studio.personal.accountTip3') }}</span>
            </li>
          </ul>
        </div>
      </el-col>
    </el-row>

    <!-- 编辑资料弹窗 -->
    <el-dialog v-model="editDialogVisible" :title="$t('studio.personal.editTitle')" width="480px" destroy-on-close>
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item :label="$t('studio.personal.username')" prop="username">
          <el-input v-model="editForm.username" :placeholder="$t('studio.personal.usernamePh')" maxlength="30" clearable />
        </el-form-item>
        <el-form-item :label="$t('studio.personal.phone')" prop="phone">
          <el-input v-model="editForm.phone" maxlength="11" clearable />
        </el-form-item>
        <el-form-item :label="$t('studio.personal.email')" prop="email">
          <el-input v-model="editForm.email" clearable />
        </el-form-item>
        <el-form-item :label="$t('studio.personal.gender')">
          <el-radio-group v-model="editForm.gender">
            <el-radio :value="1">{{ $t('studio.personal.male') }}</el-radio>
            <el-radio :value="2">{{ $t('studio.personal.female') }}</el-radio>
            <el-radio :value="0">{{ $t('studio.personal.secret') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="$t('studio.personal.bio')">
          <el-input v-model="editForm.desc" type="textarea" :rows="3" :placeholder="$t('studio.personal.bioPh')" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ $t('studio.common.actions.cancel') }}</el-button>
        <el-button type="primary" :loading="savingProfile" @click="onSubmitProfile">
          {{ $t('studio.common.actions.save') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, computed, onMounted } from 'vue'
  import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
  import { Refresh, EditPen, Camera, Key, Lock } from '@element-plus/icons-vue'
  import { useI18n } from 'vue-i18n'
  import { useUserStore } from '@/store/modules/user'

  const { t } = useI18n()
  const userStore = useUserStore()

  // 单用户部署：资料的真源是本地 user store（localStorage 持久化），不调后端
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

  const roleText = computed(() => (userInfo.roles || []).includes('admin') ? t('studio.personal.roleAdmin') : t('studio.personal.roleUser'))

  /** 把 store 缓存同步到视图 */
  const refreshFromStore = () => {
    const cached = userStore.getUserInfo
    if (!cached) return
    userInfo.userId = cached.userId || 0
    userInfo.username = cached.username || ''
    userInfo.avatar = (cached as any).avatar || ''
    userInfo.phone = (cached as any).phone || ''
    userInfo.email = (cached as any).email || ''
    userInfo.gender = (cached as any).gender ?? 0
    userInfo.desc = (cached as any).desc || ''
    userInfo.roles = cached.roles || []
  }

  /** 写回 store（persist 自动落 localStorage，顶栏头像/用户名即时同步） */
  const persistProfile = (patch: Record<string, unknown>) => {
    userStore.setUserInfo({ ...userStore.getUserInfo, ...patch } as any)
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
    username: [{ required: true, message: () => t('studio.personal.usernameRequired'), trigger: 'blur' }],
    email: [{ type: 'email', message: () => t('studio.personal.emailInvalid'), trigger: 'blur' }]
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
        persistProfile({ ...editForm })
        Object.assign(userInfo, editForm)
        ElMessage.success(t('studio.personal.saved'))
        editDialogVisible.value = false
      } finally {
        savingProfile.value = false
      }
    })
  }

  // ==================== 头像上传（本地压缩为 base64 存 store） ====================
  const avatarInputRef = ref<HTMLInputElement>()
  const uploadingAvatar = ref(false)

  const triggerAvatarUpload = () => {
    avatarInputRef.value?.click()
  }

  /** 压缩到 256px 见方的 PNG base64，避免撑爆 localStorage */
  const fileToAvatarDataUrl = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onerror = () => reject(new Error('read failed'))
      reader.onload = () => {
        const img = new Image()
        img.onerror = () => reject(new Error('decode failed'))
        img.onload = () => {
          const size = 256
          const canvas = document.createElement('canvas')
          canvas.width = size
          canvas.height = size
          const ctx = canvas.getContext('2d')
          if (!ctx) return reject(new Error('no canvas'))
          // 居中裁剪为正方形
          const side = Math.min(img.width, img.height)
          ctx.drawImage(img, (img.width - side) / 2, (img.height - side) / 2, side, side, 0, 0, size, size)
          resolve(canvas.toDataURL('image/png'))
        }
        img.src = reader.result as string
      }
      reader.readAsDataURL(file)
    })

  const onAvatarFileChange = async (event: Event) => {
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    input.value = ''
    if (!file) return
    if (file.size > 5 * 1024 * 1024) {
      ElMessage.warning(t('studio.personal.avatarTooLarge'))
      return
    }
    uploadingAvatar.value = true
    try {
      const dataUrl = await fileToAvatarDataUrl(file)
      persistProfile({ avatar: dataUrl })
      userInfo.avatar = dataUrl
      ElMessage.success(t('studio.personal.avatarUpdated'))
    } catch {
      ElMessage.error(t('studio.personal.avatarFailed'))
    } finally {
      uploadingAvatar.value = false
    }
  }

  onMounted(refreshFromStore)
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

    .account-card {
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

      .account-list {
        list-style: none;
        padding: 0;
        margin: 0;

        li {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 10px 0;
          font-size: 13px;
          line-height: 1.6;
          color: var(--el-text-color-primary);
          border-bottom: 1px dashed var(--el-border-color-lighter);

          &:last-child {
            border-bottom: none;
          }

          .el-icon {
            margin-top: 3px;
            color: var(--art-primary);
          }
        }
      }
    }
  }
</style>

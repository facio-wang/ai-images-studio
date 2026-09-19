<template>
  <div class="app-user page-container">
    <!-- 顶部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">用户列表</h2>
        <p class="page-desc">已注册的APP用户管理（封号/解封需超管或管理员，资料编辑仅超管）</p>
      </div>
      <div class="header-right">
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar art-custom-card">
      <el-form :inline="true" @submit.prevent="onSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="filter.keyword"
            placeholder="用户名/昵称/手机号/邮箱"
            clearable
            style="width: 220px"
            @keyup.enter="onSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.ban" placeholder="全部" clearable style="width: 130px">
            <el-option label="正常" :value="0" />
            <el-option label="已封禁" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 列表 -->
    <div class="table-wrap art-custom-card">
      <el-table
        v-loading="loading"
        :data="list"
        stripe
        style="width: 100%"
        :header-cell-style="{ backgroundColor: 'var(--el-fill-color-lighter)', fontWeight: '500' }"
      >
        <el-table-column label="用户" min-width="180" fixed="left">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="36" :src="getImageUrl(row.img)">
                {{ (row.nickname || row.username || '?').charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="user-cell__info">
                <div class="user-cell__name">{{ row.nickname || row.username || '-' }}</div>
                <div class="user-cell__sub">{{ row.username || '-' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.phone || '-' }}</template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.email || '-' }}</template>
        </el-table-column>
        <el-table-column prop="level" label="等级" width="70" align="center" />
        <el-table-column prop="point" label="积分" width="90" align="center" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tooltip v-if="row.is_banned === 1" :content="row.ban_reason" placement="top">
              <el-tag type="danger" size="small">已封禁</el-tag>
            </el-tooltip>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time_text" label="注册时间" min-width="150" />
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDetail(row)">详情</el-button>
            <el-button
              v-if="permissions.canBan && row.is_banned === 0 && row.id !== 1"
              type="danger"
              link
              size="small"
              @click="openBanDialog(row)"
            >
              封号
            </el-button>
            <el-button
              v-if="permissions.canBan && row.is_banned === 1"
              type="success"
              link
              size="small"
              @click="onUnban(row)"
            >
              解封
            </el-button>
            <el-button
              v-if="permissions.canEdit"
              type="warning"
              link
              size="small"
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </div>

    <!-- 封号对话框 -->
    <el-dialog v-model="banDialog.visible" title="封禁用户" width="480px" destroy-on-close>
      <el-form ref="banFormRef" :model="banDialog" :rules="banRules" label-width="80px">
        <el-form-item label="用户">
          <el-tag>{{ banDialog.nickname || banDialog.username }}（ID: {{ banDialog.id }}）</el-tag>
        </el-form-item>
        <el-form-item label="封号理由" prop="reason">
          <el-input
            v-model="banDialog.reason"
            type="textarea"
            :rows="4"
            maxlength="200"
            show-word-limit
            placeholder="请填写封号理由（必填，将同步展示给用户）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="banDialog.visible = false">取消</el-button>
        <el-button type="danger" :loading="acting" @click="onConfirmBan">确认封禁</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框（仅超管） -->
    <el-dialog v-model="editDialog.visible" title="编辑用户资料" width="560px" destroy-on-close>
      <el-form ref="editFormRef" :model="editDialog.form" :rules="editRules" label-width="90px">
        <el-form-item label="头像">
          <div class="avatar-edit">
            <el-avatar :size="64" :src="getImageUrl(editDialog.form.img)">
              {{ (editDialog.form.nickname || editDialog.form.username || '?').charAt(0).toUpperCase() }}
            </el-avatar>
            <div class="avatar-edit__actions">
              <el-button size="small" :loading="uploading" @click="triggerAvatarUpload">
                {{ editDialog.form.img ? '更换头像' : '上传头像' }}
              </el-button>
              <el-button v-if="editDialog.form.img" size="small" text type="danger" @click="editDialog.form.img = ''">
                移除
              </el-button>
            </div>
            <input
              ref="avatarInputRef"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              style="display: none"
              @change="onAvatarFileChange"
            />
          </div>
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editDialog.form.username" maxlength="30" clearable />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="editDialog.form.nickname" maxlength="30" clearable />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="editDialog.form.realname" maxlength="30" clearable />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editDialog.form.phone" maxlength="11" clearable />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editDialog.form.email" clearable />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="editDialog.form.gender">
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
            <el-radio :value="0">保密</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="年龄">
          <el-input-number v-model="editDialog.form.age" :min="0" :max="150" />
        </el-form-item>
        <el-form-item label="生日">
          <el-date-picker
            v-model="editDialog.form.birthday"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择生日"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="积分">
          <el-input-number v-model="editDialog.form.point" :min="0" />
        </el-form-item>
        <el-form-item label="等级">
          <el-input-number v-model="editDialog.form.level" :min="1" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="onSubmitEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉：全量数据 -->
    <el-drawer v-model="detailDrawer.visible" title="用户详情" size="560px" destroy-on-close>
      <div v-loading="detailDrawer.loading" class="detail-body">
        <template v-if="detailDrawer.data">
          <!-- 基础信息 -->
          <h4 class="detail-section-title">基础信息</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="用户ID">{{ detailDrawer.data.user.id }}</el-descriptions-item>
            <el-descriptions-item label="用户名">{{ detailDrawer.data.user.username || '-' }}</el-descriptions-item>
            <el-descriptions-item label="昵称">{{ detailDrawer.data.user.nickname || '-' }}</el-descriptions-item>
            <el-descriptions-item label="真实姓名">{{ detailDrawer.data.user.realname || '-' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ detailDrawer.data.user.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ detailDrawer.data.user.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="性别">
              {{ { 0: '保密', 1: '男', 2: '女' }[detailDrawer.data.user.gender] ?? '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="年龄">{{ detailDrawer.data.user.age || '-' }}</el-descriptions-item>
            <el-descriptions-item label="生日">{{ detailDrawer.data.user.birthday || '-' }}</el-descriptions-item>
            <el-descriptions-item label="等级">{{ detailDrawer.data.user.level }}</el-descriptions-item>
            <el-descriptions-item label="积分">{{ detailDrawer.data.user.point }}</el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ detailDrawer.data.user.create_time_text || '-' }}</el-descriptions-item>
            <el-descriptions-item label="更新时间" :span="2">{{ detailDrawer.data.user.update_time_text || '-' }}</el-descriptions-item>
          </el-descriptions>

          <!-- 封禁信息 -->
          <h4 class="detail-section-title">封禁状态</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="状态">
              <el-tag v-if="detailDrawer.data.user.is_banned === 1" type="danger" size="small">已封禁</el-tag>
              <el-tag v-else type="success" size="small">正常</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="detailDrawer.data.user.is_banned === 1" label="封号理由">
              {{ detailDrawer.data.user.ban_reason || '-' }}
            </el-descriptions-item>
            <el-descriptions-item v-if="detailDrawer.data.user.is_banned === 1" label="封禁时间">
              {{ detailDrawer.data.user.banned_at_text || '-' }}
            </el-descriptions-item>
            <el-descriptions-item v-if="detailDrawer.data.user.is_banned === 1" label="操作人">
              {{ detailDrawer.data.user.ban_operator_name || '-' }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 业务统计 -->
          <h4 class="detail-section-title">业务数据</h4>
          <div class="stats-grid">
            <div class="stats-item">
              <div class="stats-item__num">{{ detailDrawer.data.stats.friend_count }}</div>
              <div class="stats-item__label">好友</div>
            </div>
            <div class="stats-item">
              <div class="stats-item__num">{{ detailDrawer.data.stats.schedule_count }}</div>
              <div class="stats-item__label">日程</div>
            </div>
            <div class="stats-item">
              <div class="stats-item__num">{{ detailDrawer.data.stats.goal_count }}</div>
              <div class="stats-item__label">目标</div>
            </div>
            <div class="stats-item">
              <div class="stats-item__num">{{ detailDrawer.data.stats.chat_msg_count }}</div>
              <div class="stats-item__label">聊天消息</div>
            </div>
            <div class="stats-item">
              <div class="stats-item__num">{{ detailDrawer.data.stats.ai_chat_count }}</div>
              <div class="stats-item__label">AI对话</div>
            </div>
          </div>

          <!-- 微信绑定 -->
          <h4 class="detail-section-title">微信绑定</h4>
          <el-descriptions v-if="detailDrawer.data.wechat" :column="1" border size="small">
            <el-descriptions-item label="OpenID">{{ detailDrawer.data.wechat.open_id }}</el-descriptions-item>
            <el-descriptions-item label="绑定昵称">{{ detailDrawer.data.wechat.nickname || '-' }}</el-descriptions-item>
            <el-descriptions-item label="绑定手机">{{ detailDrawer.data.wechat.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="绑定时间">{{ detailDrawer.data.wechat.create_time_text || '-' }}</el-descriptions-item>
          </el-descriptions>
          <el-empty v-else description="未绑定微信" :image-size="60" />

          <!-- 技术信息 -->
          <h4 class="detail-section-title">其他</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="推送CID">{{ detailDrawer.data.user.push_cid || '-' }}</el-descriptions-item>
          </el-descriptions>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted } from 'vue'
  import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
  import { Refresh } from '@element-plus/icons-vue'
  import { AppUserService, type AppUserItem, type AppUserPermissions, type AppUserDetailData } from '@/api/appUserApi'
  import { uploadService } from '@/api/uploadApi'

  defineOptions({ name: 'OperationAppUser' })

  /** 后端存的相对路径头像补全域名 */
  const getImageUrl = (url: string) => {
    if (!url) return ''
    return /^https?:\/\//.test(url) ? url : `${import.meta.env.VITE_API_URL}/storage/${url.replace(/^\/+/, '')}`
  }

  /* ---------------- 列表 ---------------- */
  const loading = ref(false)
  const list = ref<AppUserItem[]>([])
  const pagination = reactive({ page: 1, size: 20, total: 0 })
  const filter = reactive<{ keyword: string; ban: number | string }>({ keyword: '', ban: '' })
  const permissions = ref<AppUserPermissions>({ roleId: 0, canBan: false, canEdit: false })

  const fetchList = async () => {
    loading.value = true
    try {
      const res = await AppUserService.getList({
        page: pagination.page,
        size: pagination.size,
        keyword: filter.keyword || undefined,
        ban: filter.ban === '' ? undefined : filter.ban
      })
      const payload = res?.data
      if (payload) {
        list.value = payload.list || []
        pagination.total = payload.total || 0
        permissions.value = payload.permissions || permissions.value
      } else {
        list.value = []
        pagination.total = 0
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      loading.value = false
    }
  }

  const onSearch = () => {
    pagination.page = 1
    fetchList()
  }

  const resetFilter = () => {
    filter.keyword = ''
    filter.ban = ''
    pagination.page = 1
    fetchList()
  }

  /* ---------------- 封号/解封 ---------------- */
  const acting = ref(false)
  const banDialog = reactive<{ visible: boolean; id: number; username: string; nickname: string; reason: string }>({
    visible: false,
    id: 0,
    username: '',
    nickname: '',
    reason: ''
  })
  const banFormRef = ref<FormInstance>()
  const banRules: FormRules = {
    reason: [{ required: true, message: '请填写封号理由', trigger: 'blur' }]
  }

  const openBanDialog = (row: AppUserItem) => {
    Object.assign(banDialog, { visible: true, id: row.id, username: row.username, nickname: row.nickname, reason: '' })
  }

  const onConfirmBan = async () => {
    if (!banFormRef.value) return
    await banFormRef.value.validate(async (valid) => {
      if (!valid) return
      acting.value = true
      try {
        const res = await AppUserService.ban(banDialog.id, banDialog.reason)
        if (res?.code === 0) {
          ElMessage.success('已封禁')
          banDialog.visible = false
          fetchList()
        } else {
          ElMessage.error(res?.msg || '封禁失败')
        }
      } catch (e) {
        // 错误已由 http 拦截器提示
      } finally {
        acting.value = false
      }
    })
  }

  const onUnban = async (row: AppUserItem) => {
    try {
      await ElMessageBox.confirm(
        `确认解除对用户「${row.nickname || row.username}」的封禁？`,
        '解除封禁',
        { type: 'warning' }
      )
    } catch (e) {
      return
    }
    acting.value = true
    try {
      const res = await AppUserService.unban(row.id)
      if (res?.code === 0) {
        ElMessage.success('已解除封禁')
        fetchList()
      } else {
        ElMessage.error(res?.msg || '解封失败')
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      acting.value = false
    }
  }

  /* ---------------- 编辑（仅超管） ---------------- */
  const editDialog = reactive<{ visible: boolean; form: Record<string, any> }>({
    visible: false,
    form: {}
  })
  const editFormRef = ref<FormInstance>()
  const editRules: FormRules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    phone: [
      { pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }
    ],
    email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }]
  }

  const openEditDialog = (row: AppUserItem) => {
    editDialog.form = {
      id: row.id,
      username: row.username || '',
      nickname: row.nickname || '',
      realname: row.realname || '',
      phone: row.phone || '',
      email: row.email || '',
      gender: row.gender ?? 0,
      age: row.age ?? 0,
      birthday: row.birthday || '',
      point: row.point ?? 0,
      level: row.level ?? 1,
      img: row.img || ''
    }
    editDialog.visible = true
  }

  const onSubmitEdit = async () => {
    if (!editFormRef.value) return
    await editFormRef.value.validate(async (valid) => {
      if (!valid) return
      acting.value = true
      try {
        const { id, ...data } = editDialog.form
        const res = await AppUserService.save(id, data)
        if (res?.code === 0) {
          ElMessage.success('保存成功')
          editDialog.visible = false
          fetchList()
        } else {
          ElMessage.error(res?.msg || '保存失败')
        }
      } catch (e) {
        // 错误已由 http 拦截器提示
      } finally {
        acting.value = false
      }
    })
  }

  /* 头像上传（走通用上传接口, 生效云储存） */
  const avatarInputRef = ref<HTMLInputElement>()
  const uploading = ref(false)
  const triggerAvatarUpload = () => avatarInputRef.value?.click()
  const onAvatarFileChange = async (event: Event) => {
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    input.value = ''
    if (!file) return
    if (file.size > 5 * 1024 * 1024) {
      ElMessage.warning('头像图片不能超过5M')
      return
    }
    uploading.value = true
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
      editDialog.form.img = url
      ElMessage.success('头像已上传，保存后生效')
    } catch (e: any) {
      ElMessage.error(e?.message || '头像上传失败')
    } finally {
      uploading.value = false
    }
  }

  /* ---------------- 详情抽屉 ---------------- */
  const detailDrawer = reactive<{ visible: boolean; loading: boolean; data: AppUserDetailData | null }>({
    visible: false,
    loading: false,
    data: null
  })

  const openDetail = async (row: AppUserItem) => {
    detailDrawer.visible = true
    detailDrawer.loading = true
    detailDrawer.data = null
    try {
      const res = await AppUserService.getDetail(row.id)
      detailDrawer.data = res?.data || null
    } catch (e) {
      ElMessage.error('加载详情失败')
    } finally {
      detailDrawer.loading = false
    }
  }

  onMounted(() => {
    fetchList()
  })
</script>

<style lang="scss" scoped>
  .app-user {
    padding: 16px;

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;

      .page-title {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
      }

      .page-desc {
        margin: 4px 0 0;
        font-size: 13px;
        color: var(--art-gray-text-800);
      }
    }

    .filter-bar {
      padding: 16px;
      margin-bottom: 16px;
      border-radius: 8px;
    }

    .table-wrap {
      padding: 16px;
      border-radius: 8px;

      .pagination-wrap {
        display: flex;
        justify-content: flex-end;
        margin-top: 16px;
      }
    }

    .user-cell {
      display: flex;
      align-items: center;
      gap: 10px;

      &__name {
        font-weight: 500;
      }

      &__sub {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }

    .avatar-edit {
      display: flex;
      align-items: center;
      gap: 12px;

      &__actions {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;

        .el-button + .el-button {
          margin-left: 0;
        }
      }
    }

    .detail-body {
      padding: 0 4px;

      .detail-section-title {
        margin: 18px 0 10px;
        font-size: 14px;
        font-weight: 600;

        &:first-child {
          margin-top: 0;
        }
      }

      .stats-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;

        .stats-item {
          padding: 12px 4px;
          text-align: center;
          border-radius: 8px;
          background-color: var(--el-fill-color-lighter);

          &__num {
            font-size: 20px;
            font-weight: 700;
          }

          &__label {
            margin-top: 4px;
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
</style>

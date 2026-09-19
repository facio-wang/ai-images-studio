<template>
  <div class="user-manage page-container">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">管理员管理</h2>
        <p class="page-desc">管理系统管理员账号与角色分配</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="openCreateModal">新增管理员</el-button>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-bar art-custom-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="fetchList">
        <el-form-item label="手机号">
          <el-input
            v-model="filterForm.phone"
            placeholder="请输入手机号"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="2" />
            <el-option label="注销" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 表格 -->
    <div class="table-wrap art-custom-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        style="width: 100%"
        :header-cell-style="{ backgroundColor: 'var(--el-fill-color-lighter)', fontWeight: '500' }"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="phone" label="手机号" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.phone || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="130">
          <template #default="{ row }">
            <el-tag :type="row.role_id === 1 ? 'danger' : row.role_id === 2 ? 'warning' : 'info'">
              {{ row.role_title || row.role_name || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status_lable || statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="170" />
        <el-table-column label="操作" width="240" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              :icon="Edit"
              @click="openEditModal(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.role_id !== 1"
              :type="row.status === 1 ? 'warning' : 'success'"
              link
              size="small"
              @click="handleToggle(row)"
            >
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button
              v-if="row.role_id !== 1"
              type="danger"
              link
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
            <el-tag v-else type="info" size="small" style="margin-left: 8px">超管保护</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="modalVisible"
      :title="isEdit ? '编辑管理员' : '新增管理员'"
      width="520px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="90px"
        @submit.prevent
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" :disabled="isEdit" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="留空则默认 123456"
            show-password
          />
        </el-form-item>
        <el-form-item v-else label="新密码">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="留空则不修改密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="formData.role_id" placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="role in roleOptions"
              :key="role.id"
              :label="`${role.title} (${role.name})`"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.desc" type="textarea" :rows="2" placeholder="备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modalVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted } from 'vue'
  import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
  import { Plus, Edit, Delete, Refresh } from '@element-plus/icons-vue'
  import {
    AdminManageService,
    RoleManageService,
    type AdminItem,
    type AdminSaveParams,
    type RoleItem
  } from '@/api/systemApi'

  defineOptions({ name: 'SystemUser' })

  // ===== 列表数据 =====
  const loading = ref(false)
  const tableData = ref<AdminItem[]>([])
  const pagination = reactive({ page: 1, size: 10, total: 0 })
  const filterForm = reactive({ phone: '', status: undefined as number | undefined })

  // 角色下拉选项
  const roleOptions = ref<RoleItem[]>([])

  // 状态文案
  const statusText = (s: number) => ({ 1: '启用', 2: '禁用', 3: '注销' }[s] ?? '-')

  // 拉取管理员列表
  async function fetchList() {
    loading.value = true
    try {
      const res = await AdminManageService.getList({
        page: pagination.page,
        size: pagination.size,
        phone: filterForm.phone || undefined,
        status: filterForm.status
      })
      const payload = res?.data
      if (payload) {
        tableData.value = payload.data || []
        pagination.total = payload.total || 0
      } else {
        tableData.value = []
        pagination.total = 0
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      loading.value = false
    }
  }

  // 拉取角色选项
  async function fetchRoles() {
    try {
      const res = await RoleManageService.getList()
      roleOptions.value = res?.data || []
    } catch (e) {
      // ignore
    }
  }

  function resetFilter() {
    filterForm.phone = ''
    filterForm.status = undefined
    pagination.page = 1
    fetchList()
  }

  // ===== 新增/编辑弹窗 =====
  const modalVisible = ref(false)
  const isEdit = ref(false)
  const submitting = ref(false)
  const formRef = ref<FormInstance>()

  const createDefaultForm = (): AdminSaveParams => ({
    username: '',
    password: '',
    phone: '',
    email: '',
    role_id: 2,
    status: 1,
    desc: ''
  })

  const formData = reactive<AdminSaveParams>(createDefaultForm())

  const formRules: FormRules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    role_id: [{ required: true, message: '请选择角色', trigger: 'change' }],
    password: [
      {
        validator: (_rule, value: string, callback) => {
          if (!isEdit.value && !value) {
            // 新增时允许留空（默认 123456）
            callback()
            return
          }
          if (value && value.length < 6) {
            callback(new Error('密码至少 6 位'))
            return
          }
          callback()
        },
        trigger: 'blur'
      }
    ]
  }

  function openCreateModal() {
    isEdit.value = false
    Object.assign(formData, createDefaultForm())
    modalVisible.value = true
  }

  function openEditModal(row: AdminItem) {
    isEdit.value = true
    Object.assign(formData, {
      id: row.id,
      username: row.username,
      password: '',
      phone: row.phone || '',
      email: row.email || '',
      role_id: row.role_id,
      status: row.status,
      desc: row.desc || ''
    })
    modalVisible.value = true
  }

  function resetForm() {
    Object.assign(formData, createDefaultForm())
    formRef.value?.clearValidate()
  }

  async function handleSubmit() {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
      if (!valid) return
      submitting.value = true
      try {
        const res = await AdminManageService.save({ ...formData })
        if (res?.code === 0) {
          ElMessage.success(isEdit.value ? '编辑成功' : '新增成功')
          modalVisible.value = false
          fetchList()
        } else {
          ElMessage.error(res?.msg || '操作失败')
        }
      } catch (e) {
        // ignore
      } finally {
        submitting.value = false
      }
    })
  }

  // ===== 启用/禁用 =====
  async function handleToggle(row: AdminItem) {
    const action = row.status === 1 ? '禁用' : '启用'
    try {
      await ElMessageBox.confirm(`确定${action}管理员「${row.username}」吗？`, '提示', {
        type: 'warning'
      })
      const res = await AdminManageService.toggle(row.id)
      if (res?.code === 0) {
        ElMessage.success(`${action}成功`)
        fetchList()
      } else {
        ElMessage.error(res?.msg || `${action}失败`)
      }
    } catch (e) {
      // 用户取消
    }
  }

  // ===== 删除 =====
  async function handleDelete(row: AdminItem) {
    try {
      await ElMessageBox.confirm(
        `确定删除管理员「${row.username}」吗？此操作不可恢复。`,
        '删除确认',
        { type: 'warning' }
      )
      const res = await AdminManageService.remove(row.id)
      if (res?.code === 0) {
        ElMessage.success('删除成功')
        fetchList()
      } else {
        ElMessage.error(res?.msg || '删除失败')
      }
    } catch (e) {
      // 用户取消
    }
  }

  onMounted(() => {
    fetchRoles()
    fetchList()
  })
</script>

<style lang="scss" scoped>
  .user-manage {
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
  }
</style>

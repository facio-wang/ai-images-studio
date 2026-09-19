<template>
  <div class="role-manage page-container">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">角色管理</h2>
        <p class="page-desc">管理角色与菜单权限分配</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="openCreateModal">新增角色</el-button>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
      </div>
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
        <el-table-column prop="name" label="角色标识" min-width="130" show-overflow-tooltip />
        <el-table-column prop="title" label="标题" min-width="120" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="菜单数" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.menu_count ?? row.menu_ids?.length ?? 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" :icon="Edit" @click="openEditModal(row)">
              编辑
            </el-button>
            <el-button type="warning" link size="small" :icon="Key" @click="openAssignModal(row)">
              分配菜单
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              :icon="Delete"
              :disabled="row.id === 1"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
            <el-tag v-if="row.id === 1" type="info" size="small" style="margin-left: 8px">超管</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="modalVisible"
      :title="isEdit ? '编辑角色' : '新增角色'"
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
        <el-form-item label="角色标识" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="如 operator / pleb"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="如 运营 / 只读" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="角色说明" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch v-model="formData.status" :active-value="1" :inactive-value="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modalVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分配菜单弹窗 -->
    <el-dialog
      v-model="assignVisible"
      title="分配菜单权限"
      width="420px"
      :close-on-click-modal="false"
    >
      <div v-loading="menuLoading" class="menu-tree-wrap">
        <el-tree
          ref="menuTreeRef"
          :data="menuTree"
          show-checkbox
          node-key="id"
          :props="{ label: 'title', children: 'children' }"
          :default-checked-keys="checkedMenuIds"
          default-expand-all
        />
      </div>
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :loading="assigning" @click="handleAssignSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted } from 'vue'
  import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
  import { Plus, Edit, Delete, Refresh, Key } from '@element-plus/icons-vue'
  import { RoleManageService, type RoleItem } from '@/api/systemApi'
  import { menuService } from '@/api/menuApi'

  defineOptions({ name: 'SystemRole' })

  // ===== 列表数据 =====
  const loading = ref(false)
  const tableData = ref<RoleItem[]>([])

  async function fetchList() {
    loading.value = true
    try {
      const res = await RoleManageService.getList()
      tableData.value = res?.data ?? []
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      loading.value = false
    }
  }

  // ===== 新增/编辑弹窗 =====
  const modalVisible = ref(false)
  const isEdit = ref(false)
  const submitting = ref(false)
  const formRef = ref<FormInstance>()

  const createDefaultForm = () => ({
    name: '',
    title: '',
    description: '',
    status: 1
  })

  const formData = reactive(createDefaultForm())

  const formRules: FormRules = {
    name: [{ required: true, message: '请输入角色标识', trigger: 'blur' }],
    title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
  }

  function openCreateModal() {
    isEdit.value = false
    Object.assign(formData, createDefaultForm())
    modalVisible.value = true
  }

  function openEditModal(row: RoleItem) {
    isEdit.value = true
    Object.assign(formData, {
      id: row.id,
      name: row.name,
      title: row.title,
      description: row.description || '',
      status: row.status
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
        const res = isEdit.value
          ? await RoleManageService.update({ ...formData })
          : await RoleManageService.save({ ...formData })
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

  // ===== 删除 =====
  async function handleDelete(row: RoleItem) {
    try {
      await ElMessageBox.confirm(
        `确定删除角色「${row.title}」吗？删除后不可恢复。`,
        '删除确认',
        { type: 'warning' }
      )
      const res = await RoleManageService.remove(row.id)
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

  // ===== 分配菜单 =====
  const assignVisible = ref(false)
  const assigning = ref(false)
  const menuLoading = ref(false)
  const menuTreeRef = ref<any>()
  const menuTree = ref<any[]>([])
  const checkedMenuIds = ref<number[]>([])
  const currentRoleId = ref(0)

  async function openAssignModal(row: RoleItem) {
    currentRoleId.value = row.id
    assignVisible.value = true
    menuLoading.value = true
    try {
      // 并行拉取完整菜单树 + 该角色已分配的菜单ID
      const [treeRes, menusRes] = await Promise.all([
        menuService.getAllMenus(),
        RoleManageService.getMenus(row.id)
      ])
      menuTree.value = treeRes ?? []
      checkedMenuIds.value = menusRes?.data?.menu_ids ?? []
      // 让 el-tree 重新加载后正确回显
      nextTick(() => {
        menuTreeRef.value?.setCheckedKeys(checkedMenuIds.value)
      })
    } catch (e) {
      ElMessage.error('加载菜单失败')
    } finally {
      menuLoading.value = false
    }
  }

  async function handleAssignSubmit() {
    const checked = menuTreeRef.value?.getCheckedKeys() as number[]
    const halfChecked = menuTreeRef.value?.getHalfCheckedKeys() as number[]
    const menuIds = [...new Set([...checked, ...halfChecked])]
    assigning.value = true
    try {
      const res = await RoleManageService.assignMenus({
        id: currentRoleId.value,
        menu_ids: menuIds
      })
      if (res?.code === 0) {
        ElMessage.success('菜单权限已更新')
        assignVisible.value = false
        fetchList()
      } else {
        ElMessage.error(res?.msg || '分配失败')
      }
    } catch (e) {
      // ignore
    } finally {
      assigning.value = false
    }
  }

  onMounted(() => {
    fetchList()
  })
</script>

<style lang="scss" scoped>
  .role-manage {
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

    .table-wrap {
      padding: 16px;
      border-radius: 8px;
    }

    .menu-tree-wrap {
      min-height: 200px;
      max-height: 360px;
      overflow-y: auto;
      padding: 8px;
    }
  }
</style>

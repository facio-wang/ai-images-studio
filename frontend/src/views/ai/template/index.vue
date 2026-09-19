<template>
  <div class="ai-template page-container">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">AI模板管理</h2>
        <p class="page-desc">管理 AI 助手的提示词模板</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="openCreateModal">新增模板</el-button>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-bar art-custom-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="fetchList">
        <el-form-item label="类型">
          <el-input
            v-model="filterForm.type"
            placeholder="按类型筛选，如 schedule/plan"
            clearable
            style="width: 240px"
          />
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
        <el-table-column prop="type" label="类型" min-width="120" show-overflow-tooltip />
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="字段数" width="90" align="center">
          <template #default="{ row }">
            {{ Array.isArray(row.fields) ? row.fields.length : 0 }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.isActive === 1 ? 'success' : 'info'">
              {{ row.isActive === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort" label="排序" width="80" align="center" />
        <el-table-column prop="createdAt" label="创建时间" min-width="170" show-overflow-tooltip />
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
              :type="row.isActive === 1 ? 'warning' : 'success'"
              link
              size="small"
              @click="handleToggle(row)"
            >
              {{ row.isActive === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
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
      :title="isEdit ? '编辑模板' : '新增模板'"
      width="640px"
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
        <el-form-item label="类型" prop="type">
          <el-select
            v-model="formData.type"
            placeholder="请选择或输入类型"
            filterable
            allow-create
            default-first-option
            style="width: 100%"
          >
            <el-option label="日程 (schedule)" value="schedule" />
            <el-option label="计划 (plan)" value="plan" />
            <el-option label="对话 (chat)" value="chat" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="8"
            placeholder="提示词模板，支持 {变量} 占位，例如：请根据 {title} 安排日程..."
          />
        </el-form-item>
        <el-form-item label="字段" prop="fieldsText">
          <el-input
            v-model="formData.fieldsText"
            type="textarea"
            :rows="3"
            placeholder='输入 JSON 数组，如 ["title","start_time"]'
          />
        </el-form-item>
        <el-form-item label="启用" prop="is_active">
          <el-switch v-model="formData.is_active" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="排序" prop="sort">
          <el-input-number v-model="formData.sort" :min="0" :step="1" controls-position="right" />
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
    AiTemplateService,
    type AiTemplateItem,
    type AiTemplateSaveParams
  } from '@/api/templateApi'

  defineOptions({ name: 'AiTemplate' })

  // 表单数据结构（含 fieldsText 用于 textarea 输入）
  interface TemplateFormState {
    id?: number
    type: string
    name: string
    content: string
    fieldsText: string
    is_active: number
    sort: number
  }

  // ===== 列表数据 =====
  const loading = ref(false)
  const tableData = ref<AiTemplateItem[]>([])
  const pagination = reactive({ page: 1, size: 20, total: 0 })
  const filterForm = reactive({ type: '' })

  // 拉取模板列表
  async function fetchList() {
    loading.value = true
    try {
      const res = await AiTemplateService.getList({
        page: pagination.page,
        size: pagination.size,
        type: filterForm.type || undefined
      })
      const payload = res?.data
      if (payload) {
        tableData.value = payload.list ?? []
        pagination.total = payload.total ?? 0
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

  function resetFilter() {
    filterForm.type = ''
    pagination.page = 1
    fetchList()
  }

  // ===== 新增/编辑弹窗 =====
  const modalVisible = ref(false)
  const isEdit = ref(false)
  const submitting = ref(false)
  const formRef = ref<FormInstance>()

  const createDefaultForm = (): TemplateFormState => ({
    type: '',
    name: '',
    content: '',
    fieldsText: '[]',
    is_active: 1,
    sort: 0
  })

  const formData = reactive<TemplateFormState>(createDefaultForm())

  const formRules: FormRules = {
    type: [{ required: true, message: '请选择或输入类型', trigger: 'change' }],
    name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
    content: [{ required: true, message: '请输入模板内容', trigger: 'blur' }],
    fieldsText: [
      {
        validator: (_rule, value: string, callback) => {
          if (!value) {
            callback()
            return
          }
          try {
            const parsed = JSON.parse(value)
            if (!Array.isArray(parsed)) {
              callback(new Error('字段必须是 JSON 数组'))
              return
            }
            callback()
          } catch (e) {
            callback(new Error('字段格式非法，请输入合法的 JSON 数组'))
          }
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

  function openEditModal(row: AiTemplateItem) {
    isEdit.value = true
    Object.assign(formData, {
      id: row.id,
      type: row.type,
      name: row.name,
      content: row.content,
      fieldsText: JSON.stringify(row.fields ?? []),
      is_active: row.isActive,
      sort: row.sort
    })
    modalVisible.value = true
  }

  function resetForm() {
    Object.assign(formData, createDefaultForm())
    formRef.value?.clearValidate()
  }

  // 解析 fieldsText 为字符串数组
  function parseFields(): string[] | null {
    const text = (formData.fieldsText || '').trim()
    if (!text) return []
    try {
      const parsed = JSON.parse(text)
      if (!Array.isArray(parsed)) return null
      return parsed.map((f) => String(f))
    } catch (e) {
      return null
    }
  }

  async function handleSubmit() {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
      if (!valid) return
      // 提交前再次校验 fields（双重保险）
      const fields = parseFields()
      if (fields === null) {
        ElMessage.error('字段格式非法，请输入合法的 JSON 数组')
        return
      }
      submitting.value = true
      try {
        const payload: AiTemplateSaveParams = {
          type: formData.type,
          name: formData.name,
          content: formData.content,
          fields,
          is_active: formData.is_active,
          sort: formData.sort
        }
        let res
        if (isEdit.value && formData.id) {
          res = await AiTemplateService.update({ id: formData.id, ...payload })
        } else {
          res = await AiTemplateService.save(payload)
        }
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

  // ===== 启用/禁用切换 =====
  async function handleToggle(row: AiTemplateItem) {
    const action = row.isActive === 1 ? '禁用' : '启用'
    try {
      await ElMessageBox.confirm(`确定${action}模板「${row.name}」吗？`, '提示', {
        type: 'warning'
      })
      const res = await AiTemplateService.update({
        id: row.id,
        is_active: row.isActive === 1 ? 0 : 1
      })
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
  async function handleDelete(row: AiTemplateItem) {
    try {
      await ElMessageBox.confirm(
        `确定删除模板「${row.name}」吗？此操作不可恢复。`,
        '删除确认',
        { type: 'warning' }
      )
      const res = await AiTemplateService.remove(row.id)
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
    fetchList()
  })
</script>

<style lang="scss" scoped>
  .ai-template {
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

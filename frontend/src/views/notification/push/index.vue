<template>
  <div class="notification-push page-container">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">通知推送管理</h2>
        <p class="page-desc">向APP在线用户广播系统通知（WebSocket实时推送）</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="openCreateModal">新建推送</el-button>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-bar art-custom-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="onSearch">
        <el-form-item label="类型">
          <el-select v-model="filterForm.type" placeholder="全部类型" clearable style="width: 140px">
            <el-option label="系统通知" value="system" />
            <el-option label="社交通知" value="social" />
            <el-option label="营销推广" value="marketing" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="草稿" :value="0" />
            <el-option label="已发送" :value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="filterForm.title" placeholder="标题关键词" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
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
        <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
        <el-table-column label="类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="typeTagType(row.type)">{{ typeText(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.targetType === 'all' ? 'success' : 'warning'">
              {{ row.targetType === 'all' ? '全员' : '指定用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发送方式" width="120" align="center">
          <template #default="{ row }">
            {{ sendTypeText(row.sendType) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '已发送' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发送时间" min-width="170">
          <template #default="{ row }">
            {{ row.sendTime ? formatTime(row.sendTime) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== 1"
              type="success"
              link
              size="small"
              :loading="sendingId === row.id"
              @click="handleSend(row)"
            >
              发送
            </el-button>
            <el-button type="primary" link size="small" @click="openViewModal(row)">查看</el-button>
            <el-button type="danger" link size="small" :icon="Delete" @click="handleDelete(row)">
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

    <!-- 新建弹窗 -->
    <el-dialog
      v-model="modalVisible"
      title="新建推送"
      width="820px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px" @submit.prevent>
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="推送标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <!-- 2026-08-31: 富文本编辑器(后台支持图文混排推送), APP通知详情页以rich-text渲染 -->
          <ArtWangEditor v-model="formData.content" class="push-editor" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="系统通知" value="system" />
            <el-option label="社交通知" value="social" />
            <el-option label="营销推广" value="marketing" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标" prop="target_type">
          <el-radio-group v-model="formData.target_type">
            <el-radio value="all">全员</el-radio>
            <el-radio value="designated">指定用户</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="formData.target_type === 'designated'" label="用户ID">
          <el-input
            v-model="targetUsersInput"
            placeholder="多个用户ID用英文逗号分隔，如 1,2,3"
            clearable
          />
        </el-form-item>
        <el-form-item label="发送方式" prop="send_type">
          <el-select v-model="formData.send_type" placeholder="请选择发送方式" style="width: 100%">
            <el-option label="WebSocket（在线推送）" value="websocket" />
            <el-option label="个推（离线推送-暂未实现）" value="getui" disabled />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modalVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存草稿</el-button>
        <el-button type="success" :loading="submitting" @click="handleSubmitAndSend">保存并发送</el-button>
      </template>
    </el-dialog>

    <!-- 查看弹窗 -->
    <el-dialog v-model="viewVisible" title="推送详情" width="600px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="标题">{{ viewRow.title }}</el-descriptions-item>
        <el-descriptions-item label="内容">
          <!-- 富文本推送内容渲染 -->
          <div class="push-content-view" v-html="viewRow.content"></div>
        </el-descriptions-item>
        <el-descriptions-item label="类型">{{ typeText(viewRow.type) }}</el-descriptions-item>
        <el-descriptions-item label="目标">
          {{ viewRow.targetType === 'all' ? '全员' : '指定用户: ' + (viewRow.targetUsers || []).join(', ') }}
        </el-descriptions-item>
        <el-descriptions-item label="发送方式">{{ sendTypeText(viewRow.sendType) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          {{ viewRow.status === 1 ? '已发送' : '草稿' }}
        </el-descriptions-item>
        <el-descriptions-item label="发送时间">
          {{ viewRow.sendTime ? formatTime(viewRow.sendTime) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ viewRow.createTime ? formatTime(viewRow.createTime) : '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted } from 'vue'
  import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
  import { Plus, Delete, Refresh } from '@element-plus/icons-vue'
  import ArtWangEditor from '@/components/core/forms/ArtWangEditor.vue'
  import {
    NotificationService,
    type NotificationItem,
    type NotificationSaveParams
  } from '@/api/notificationApi'

  defineOptions({ name: 'NotificationPush' })

  // ===== 列表 =====
  const loading = ref(false)
  const tableData = ref<NotificationItem[]>([])
  const pagination = reactive({ page: 1, size: 10, total: 0 })
  const filterForm = reactive({ type: '', status: '' as number | string, title: '' })

  const sendingId = ref<number | null>(null)

  const typeText = (t?: string) =>
    ({ system: '系统通知', social: '社交通知', marketing: '营销推广' }[t ?? ''] ?? t ?? '')
  const typeTagType = (t?: string): 'warning' | 'success' | 'primary' =>
    (({ system: 'primary', social: 'warning', marketing: 'success' } as Record<string, 'warning' | 'success' | 'primary'>)[t ?? ''] ?? 'primary')
  const sendTypeText = (s?: string) =>
    ({ websocket: 'WebSocket', getui: '个推' }[s ?? ''] ?? s ?? '')

  function formatTime(ts: number | null): string {
    if (!ts) return '-'
    const d = new Date(ts * 1000)
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  }

  async function fetchList() {
    loading.value = true
    try {
      const res = await NotificationService.getList({
        page: pagination.page,
        size: pagination.size,
        type: filterForm.type || undefined,
        status: filterForm.status === '' ? undefined : Number(filterForm.status),
        title: filterForm.title || undefined
      })
      const payload = res?.data
      if (payload) {
        tableData.value = payload.list || []
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

  function onSearch() {
    pagination.page = 1
    fetchList()
  }

  function resetFilter() {
    filterForm.type = ''
    filterForm.status = ''
    filterForm.title = ''
    pagination.page = 1
    fetchList()
  }

  // ===== 新建弹窗 =====
  const modalVisible = ref(false)
  const submitting = ref(false)
  const formRef = ref<FormInstance>()
  const targetUsersInput = ref('')

  const createDefaultForm = (): NotificationSaveParams => ({
    title: '',
    content: '',
    type: 'system',
    target_type: 'all',
    target_users: [],
    send_type: 'websocket'
  })

  const formData = reactive<NotificationSaveParams>(createDefaultForm())

  const formRules: FormRules = {
    title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
    content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
    type: [{ required: true, message: '请选择类型', trigger: 'change' }],
    target_type: [{ required: true, message: '请选择目标', trigger: 'change' }],
    send_type: [{ required: true, message: '请选择发送方式', trigger: 'change' }]
  }

  function openCreateModal() {
    Object.assign(formData, createDefaultForm())
    targetUsersInput.value = ''
    modalVisible.value = true
  }

  function resetForm() {
    Object.assign(formData, createDefaultForm())
    targetUsersInput.value = ''
    formRef.value?.clearValidate()
  }

  function parseTargetUsers(): number[] {
    if (formData.target_type !== 'designated') return []
    return targetUsersInput.value
      .split(/[,，\s]+/)
      .map((s) => Number(s.trim()))
      .filter((n) => n > 0)
  }

  // 保存草稿
  async function handleSubmit() {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
      if (!valid) return
      submitting.value = true
      try {
        const data = { ...formData, target_users: parseTargetUsers() }
        const res = await NotificationService.save(data)
        if (res?.code === 0) {
          ElMessage.success('草稿已保存')
          modalVisible.value = false
          fetchList()
        } else {
          ElMessage.error(res?.msg || '保存失败')
        }
      } catch (e) {
        // 错误已由 http 拦截器提示
      } finally {
        submitting.value = false
      }
    })
  }

  // 保存并发送
  async function handleSubmitAndSend() {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
      if (!valid) return
      submitting.value = true
      try {
        const data = { ...formData, target_users: parseTargetUsers() }
        const saveRes = await NotificationService.save(data)
        if (saveRes?.code !== 0 || !saveRes.data?.id) {
          ElMessage.error(saveRes?.msg || '保存失败')
          return
        }
        const sendRes = await NotificationService.send(saveRes.data.id)
        if (sendRes?.code === 0) {
          ElMessage.success('发送成功')
          modalVisible.value = false
          fetchList()
        } else {
          ElMessage.error(sendRes?.msg || '发送失败')
          fetchList()
        }
      } catch (e) {
        // 错误已由 http 拦截器提示
      } finally {
        submitting.value = false
      }
    })
  }

  // ===== 发送（列表行内） =====
  async function handleSend(row: NotificationItem) {
    try {
      await ElMessageBox.confirm(`确定立即发送「${row.title}」吗？`, '发送确认', { type: 'warning' })
      sendingId.value = row.id
      const res = await NotificationService.send(row.id)
      if (res?.code === 0) {
        ElMessage.success('发送成功')
        fetchList()
      } else {
        ElMessage.error(res?.msg || '发送失败')
      }
    } catch (e) {
      // 用户取消
    } finally {
      sendingId.value = null
    }
  }

  // ===== 删除 =====
  async function handleDelete(row: NotificationItem) {
    try {
      await ElMessageBox.confirm(`确定删除推送「${row.title}」吗？此操作不可恢复。`, '删除确认', {
        type: 'warning'
      })
      const res = await NotificationService.remove(row.id)
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

  // ===== 查看 =====
  const viewVisible = ref(false)
  const viewRow = reactive<Partial<NotificationItem>>({})

  function openViewModal(row: NotificationItem) {
    Object.assign(viewRow, row)
    viewVisible.value = true
  }

  onMounted(() => {
    fetchList()
  })
</script>

<style lang="scss" scoped>
  .notification-push {
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

    /* 富文本编辑器: 弹窗内压缩默认700px高度 */
    .push-editor {
      width: 100%;

      :deep(.editor-wrapper) {
        z-index: 100;
      }

      :deep(.w-e-text-container) {
        height: 320px !important;
      }

      :deep(.editor-wrapper > div:last-child) {
        height: 320px !important;
      }
    }

    /* 查看弹窗富文本内容 */
    .push-content-view {
      line-height: 1.7;
      word-break: break-all;

      img {
        max-width: 100%;
      }
    }
  }
</style>

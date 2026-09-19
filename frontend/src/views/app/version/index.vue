<template>
  <div class="app-version-manage page-container">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">APP版本管理</h2>
        <p class="page-desc">管理客户端版本、APK包托管与发布状态</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="openCreateModal">新增版本</el-button>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-bar art-custom-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="fetchList">
        <el-form-item label="平台">
          <el-select
            v-model="filterForm.platform"
            placeholder="全部平台"
            clearable
            style="width: 160px"
          >
            <el-option label="Android" value="android" />
            <el-option label="iOS" value="ios" />
          </el-select>
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
        <el-table-column prop="versionName" label="版本号" width="110" />
        <el-table-column prop="versionCode" label="版本数字" width="100" align="center" />
        <el-table-column label="平台" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.platform === 'ios' ? 'warning' : 'success'">
              {{ platformText(row.platform) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下载地址" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" :href="row.downloadUrl" target="_blank" :underline="false">
              {{ row.downloadUrl || '-' }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="强制更新" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.isForceUpdate === 1 ? 'danger' : 'info'">
              {{ row.isForceUpdate === 1 ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="已发布" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.isPublished === 1 ? 'success' : 'warning'">
              {{ row.isPublished === 1 ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="文件大小" width="120" align="center">
          <template #default="{ row }">
            {{ formatFileSize(row.fileSize) }}
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" min-width="170" />
        <el-table-column label="操作" width="260" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              :type="row.isPublished === 1 ? 'warning' : 'success'"
              link
              size="small"
              @click="handleTogglePublish(row)"
            >
              {{ row.isPublished === 1 ? '取消发布' : '发布' }}
            </el-button>
            <el-button type="primary" link size="small" :icon="Edit" @click="openEditModal(row)">
              编辑
            </el-button>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="modalVisible"
      :title="isEdit ? '编辑版本' : '新增版本'"
      width="560px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        @submit.prevent
      >
        <el-form-item label="版本号" prop="version_name">
          <el-input v-model="formData.version_name" placeholder="如 1.1.0" />
        </el-form-item>
        <el-form-item label="版本数字" prop="version_code">
          <el-input-number
            v-model="formData.version_code"
            :min="1"
            :step="1"
            controls-position="right"
            style="width: 100%"
            placeholder="如 10100"
          />
        </el-form-item>
        <el-form-item label="平台" prop="platform">
          <el-select v-model="formData.platform" placeholder="请选择平台" style="width: 100%">
            <el-option label="Android" value="android" />
            <el-option label="iOS" value="ios" />
          </el-select>
        </el-form-item>
        <el-form-item label="APK包" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :on-exceed="handleExceed"
            accept=".apk"
            :disabled="uploading"
          >
            <template #trigger>
              <el-button type="primary" :icon="Upload" :disabled="uploading">选择APK文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                选择后立即上传到云端（独立接口，带进度条）；上传完成后点“确定”保存才生效，取消则不影响线上版本。{{
                  isEdit ? '上传新包保存后将替换旧包(同步删除OBS旧包)' : '也可下方手动填写下载地址'
                }}
              </div>
            </template>
          </el-upload>
          <div v-if="uploading" class="upload-progress">
            <el-progress :percentage="uploadProgress" :stroke-width="8" />
            <span class="upload-progress-text">上传中 {{ uploadProgress }}%</span>
          </div>
          <div v-else-if="uploadedUrl" class="upload-progress">
            <el-tag type="success" size="small">已上传</el-tag>
            <span class="upload-progress-text">{{ formatFileSize(uploadedFileSize) }} · 保存后生效</span>
          </div>
        </el-form-item>
        <el-form-item label="下载地址">
          <el-input
            v-model="formData.download_url"
            placeholder="未上传文件时可手动填写已托管的下载地址"
            clearable
          />
        </el-form-item>
        <el-form-item label="更新说明">
          <el-input
            v-model="formData.update_description"
            type="textarea"
            :rows="3"
            placeholder="本次更新内容"
          />
        </el-form-item>
        <el-form-item label="强制更新">
          <el-switch v-model="formData.is_force_update" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="立即发布">
          <el-switch v-model="formData.is_published" :active-value="1" :inactive-value="0" />
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
  import type { UploadInstance, UploadRawFile, UploadFile, UploadFiles } from 'element-plus'
  import { Plus, Edit, Delete, Refresh, Upload } from '@element-plus/icons-vue'
  import {
    AppVersionService,
    type AppVersionItem,
    type AppVersionFormData
  } from '@/api/appVersionApi'

  defineOptions({ name: 'AppVersion' })

  // ===== 列表数据 =====
  const loading = ref(false)
  const tableData = ref<AppVersionItem[]>([])
  const pagination = reactive({ page: 1, size: 10, total: 0 })
  const filterForm = reactive({ platform: '' })

  const platformText = (p: string) => ({ android: 'Android', ios: 'iOS' }[p] ?? p)

  // 文件大小格式化
  function formatFileSize(bytes: number | string): string {
    const n = Number(bytes) || 0
    if (n < 1024) return `${n} B`
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
    if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(2)} MB`
    return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`
  }

  async function fetchList() {
    loading.value = true
    try {
      const res = await AppVersionService.getList({
        page: pagination.page,
        size: pagination.size,
        platform: filterForm.platform || undefined
      })
      // res 为 BaseResponse：{ code, msg, data: { list, total, pageSize, currentPage } }
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
    filterForm.platform = ''
    pagination.page = 1
    fetchList()
  }

  // ===== 新增/编辑弹窗 =====
  const modalVisible = ref(false)
  const isEdit = ref(false)
  const submitting = ref(false)
  const formRef = ref<FormInstance>()
  const uploadRef = ref<UploadInstance>()

  // 当前选中的文件(原始File对象)
  const currentFile = ref<File | null>(null)

  const createDefaultForm = (): AppVersionFormData => ({
    version_name: '',
    version_code: 1,
    platform: 'android',
    download_url: '',
    update_description: '',
    is_force_update: 0,
    is_published: 0
  })

  const formData = reactive<AppVersionFormData>(createDefaultForm())

  const formRules: FormRules = {
    version_name: [{ required: true, message: '请输入版本号', trigger: 'blur' }],
    version_code: [{ required: true, message: '请输入版本数字', trigger: 'blur' }],
    platform: [{ required: true, message: '请选择平台', trigger: 'change' }]
  }

  function openCreateModal() {
    isEdit.value = false
    Object.assign(formData, createDefaultForm())
    currentFile.value = null
    modalVisible.value = true
  }

  function openEditModal(row: AppVersionItem) {
    isEdit.value = true
    Object.assign(formData, {
      id: row.id,
      version_name: row.versionName,
      version_code: row.versionCode,
      platform: row.platform,
      download_url: row.downloadUrl,
      update_description: row.updateDescription || '',
      is_force_update: row.isForceUpdate
    })
    currentFile.value = null
    modalVisible.value = true
  }

  function resetForm() {
    Object.assign(formData, createDefaultForm())
    currentFile.value = null
    uploading.value = false
    uploadProgress.value = 0
    uploadedUrl.value = ''
    uploadedFileSize.value = 0
    uploadRef.value?.clearFiles()
    formRef.value?.clearValidate()
  }

  // ===== 文件上传处理（2026-09-03改: 选择后立即独立上传, 进度条反馈; 保存仅提交url, 不再随表单传大包） =====
  const uploading = ref(false)
  const uploadProgress = ref(0)
  const uploadedUrl = ref('')
  const uploadedFileSize = ref(0)

  function handleFileChange(file: UploadFile, _files: UploadFiles) {
    if (file.raw) {
      currentFile.value = file.raw
      startUpload()
    }
  }

  function handleFileRemove() {
    currentFile.value = null
    // 清除本次上传结果; 若download_url是上传回填的则一并还原
    if (uploadedUrl.value && formData.download_url === uploadedUrl.value) {
      formData.download_url = ''
    }
    uploadedUrl.value = ''
    uploadedFileSize.value = 0
    uploadProgress.value = 0
  }

  async function startUpload() {
    if (!currentFile.value) return
    // 上传接口按 platform+version_name 命名OBS对象, 需先填好
    if (!formData.version_name) {
      ElMessage.warning('请先填写版本号，再选择APK文件上传')
      uploadRef.value?.clearFiles()
      currentFile.value = null
      return
    }
    uploading.value = true
    uploadProgress.value = 0
    uploadedUrl.value = ''
    uploadedFileSize.value = 0
    try {
      const fd = new FormData()
      fd.append('file', currentFile.value)
      fd.append('platform', formData.platform || 'android')
      fd.append('version_name', String(formData.version_name ?? ''))
      const res = await AppVersionService.uploadApk(fd, (p) => {
        uploadProgress.value = p
      })
      if (res?.code === 0 && res.data?.url) {
        uploadedUrl.value = res.data.url
        uploadedFileSize.value = Number(res.data.fileSize) || 0
        formData.download_url = res.data.url
        ElMessage.success('APK上传成功，点“确定”保存后生效')
      } else {
        ElMessage.error(res?.msg || '上传失败')
        uploadRef.value?.clearFiles()
        currentFile.value = null
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
      uploadRef.value?.clearFiles()
      currentFile.value = null
    } finally {
      uploading.value = false
    }
  }

  function handleExceed(files: File[]) {
    // 限制1个文件：替换已有
    uploadRef.value?.clearFiles()
    const first = files[0] as UploadRawFile
    uploadRef.value?.handleStart(first)
    currentFile.value = first
    startUpload()
  }

  // 构造 FormData（不再携带文件, 携带上传返回的url与大小）
  function buildFormData(): FormData {
    const fd = new FormData()
    fd.append('version_name', String(formData.version_name ?? ''))
    fd.append('version_code', String(formData.version_code ?? 0))
    fd.append('platform', formData.platform || 'android')
    if (formData.update_description !== undefined && formData.update_description !== null) {
      fd.append('update_description', formData.update_description)
    }
    fd.append('is_force_update', String(formData.is_force_update ?? 0))
    if (!isEdit.value) {
      fd.append('is_published', String(formData.is_published ?? 0))
    }
    if (formData.download_url) {
      fd.append('download_url', formData.download_url)
    }
    if (uploadedFileSize.value > 0) {
      fd.append('file_size', String(uploadedFileSize.value))
    }
    if (isEdit.value && formData.id) {
      fd.append('id', String(formData.id))
    }
    return fd
  }

  async function handleSubmit() {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
      if (!valid) return
      if (uploading.value) {
        ElMessage.warning('APK正在上传中，请等待上传完成')
        return
      }
      // 新增时：必须已上传或填写下载地址
      if (!isEdit.value && !formData.download_url) {
        ElMessage.warning('请上传APK文件或填写下载地址')
        return
      }
      submitting.value = true
      try {
        const fd = buildFormData()
        const res = isEdit.value
          ? await AppVersionService.update(fd)
          : await AppVersionService.save(fd)
        if (res?.code === 0) {
          ElMessage.success(isEdit.value ? '编辑成功' : '新增成功')
          modalVisible.value = false
          fetchList()
        } else {
          ElMessage.error(res?.msg || '操作失败')
        }
      } catch (e) {
        // 错误已由 http 拦截器提示
      } finally {
        submitting.value = false
      }
    })
  }

  // ===== 发布/取消发布 =====
  async function handleTogglePublish(row: AppVersionItem) {
    const action = row.isPublished === 1 ? '取消发布' : '发布'
    try {
      await ElMessageBox.confirm(`确定${action}版本「${row.versionName}」吗？`, '提示', {
        type: 'warning'
      })
      const res =
        row.isPublished === 1
          ? await AppVersionService.unpublish(row.id)
          : await AppVersionService.publish(row.id)
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
  async function handleDelete(row: AppVersionItem) {
    try {
      await ElMessageBox.confirm(
        `确定删除版本「${row.versionName}」吗？将同步删除OBS上的APK包，此操作不可恢复。`,
        '删除确认',
        { type: 'warning' }
      )
      const res = await AppVersionService.remove(row.id)
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
  .app-version-manage {
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

    .upload-progress {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 8px;
      width: 100%;

      .el-progress {
        flex: 1;
      }

      .upload-progress-text {
        font-size: 12px;
        color: var(--art-gray-text-800);
        white-space: nowrap;
      }
    }
  }
</style>

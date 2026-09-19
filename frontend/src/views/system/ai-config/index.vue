<template>
  <div class="ai-config page-container">
    <!-- 顶部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">AI模型配置</h2>
        <p class="page-desc">按服务商列表维护 AI 接口配置，单选设置当前生效的服务商（后端按生效配置调用）</p>
      </div>
      <div class="header-right">
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="onAdd">新增配置</el-button>
      </div>
    </div>

    <!-- 列表 -->
    <div class="table-wrap art-custom-card">
      <el-table v-loading="loading" :data="list" row-key="key" stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="服务商" min-width="110" />
        <el-table-column label="模型" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.value?.model || '-' }}</template>
        </el-table-column>
        <el-table-column label="接口地址" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.value?.base_url || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success" size="small">生效中</el-tag>
            <el-tag v-else type="info" size="small">未启用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" align="center" fixed="right">
          <template #default="{ row }">
            <el-popconfirm
              v-if="!row.is_active"
              title="设为当前生效服务商？将停用其他服务商"
              width="220"
              @confirm="onSetActive(row)"
            >
              <template #reference>
                <el-button type="success" size="small" plain :loading="acting === row.key">设为生效</el-button>
              </template>
            </el-popconfirm>
            <el-button v-else type="success" size="small" plain disabled>当前生效</el-button>
            <el-button type="primary" size="small" plain @click="onEdit(row)">编辑</el-button>
            <el-button type="warning" size="small" plain :loading="testing === row.key" @click="onTest(row)">测试</el-button>
            <el-popconfirm
              v-if="!row.is_active"
              title="确认删除该配置？"
              width="180"
              @confirm="onDelete(row)"
            >
              <template #reference>
                <el-button type="danger" size="small" plain>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无配置，点击右上角新增" />
        </template>
      </el-table>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑AI服务商配置' : '新增AI服务商配置'" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="服务商类型" prop="code">
          <el-select v-model="form.code" :disabled="isEdit" placeholder="选择服务商" style="width: 100%">
            <el-option v-for="c in codeOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型" prop="model">
          <el-input v-model="form.model" placeholder="如 deepseek-chat / glm-4.7 / ark-code-latest" clearable />
        </el-form-item>
        <el-form-item label="密钥" prop="api_key">
          <el-input v-model="form.api_key" placeholder="API Key" show-password clearable />
        </el-form-item>
        <el-form-item label="接口地址" prop="base_url">
          <el-input v-model="form.base_url" placeholder="如 https://api.deepseek.com" clearable />
        </el-form-item>
        <el-form-item label="AI头像">
          <div class="avatar-upload">
            <el-avatar :size="64" :src="form.avatar">
              {{ (form.model || 'AI').charAt(0).toUpperCase() }}
            </el-avatar>
            <div class="avatar-actions">
              <el-button size="small" :loading="uploadingAvatar" @click="triggerAvatarUpload">
                {{ form.avatar ? '更换头像' : '上传头像' }}
              </el-button>
              <el-button v-if="form.avatar" size="small" text type="danger" @click="form.avatar = ''">移除</el-button>
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
        <el-form-item label="System Prompt">
          <el-input v-model="form.system_prompt" type="textarea" :rows="4" placeholder="AI系统提示词（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted } from 'vue'
  import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
  import { Refresh, Plus } from '@element-plus/icons-vue'
  import { ConfigService, type ProviderItem } from '@/api/configApi'
  import { uploadService } from '@/api/uploadApi'

  defineOptions({ name: 'SystemAiConfig' })

  const AI_CODES = [
    { value: 'deepseek', label: 'DeepSeek' },
    { value: 'zhipu', label: '智谱GLM' },
    { value: 'volcengine', label: '火山方舟' },
    { value: 'kimi', label: 'Kimi' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'qwen', label: '通义千问' },
    { value: 'openai_compat', label: 'OpenAI兼容' }
  ]

  const loading = ref(false)
  const saving = ref(false)
  const testing = ref<string | ''>('')
  const acting = ref<string | ''>('')
  const list = ref<ProviderItem[]>([])

  const dialogVisible = ref(false)
  const isEdit = ref(false)
  const formRef = ref<FormInstance>()
  const form = reactive<Record<string, any>>({
    code: '',
    model: '',
    api_key: '',
    base_url: '',
    avatar: '',
    system_prompt: ''
  })

  const codeOptions = AI_CODES

  const rules: FormRules = {
    code: [{ required: true, message: '请选择服务商类型', trigger: 'change' }],
    model: [{ required: true, message: '请输入模型名', trigger: 'blur' }],
    api_key: [{ required: true, message: '请输入API密钥', trigger: 'blur' }],
    base_url: [{ required: true, message: '请输入接口地址', trigger: 'blur' }]
  }

  const fetchList = async () => {
    loading.value = true
    try {
      const res = await ConfigService.providerList('ai')
      list.value = res?.data || []
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      loading.value = false
    }
  }

  const onAdd = () => {
    isEdit.value = false
    Object.assign(form, { code: '', model: '', api_key: '', base_url: '', avatar: '', system_prompt: '' })
    dialogVisible.value = true
  }

  const onEdit = (row: ProviderItem) => {
    isEdit.value = true
    const v = row.value || {}
    Object.assign(form, {
      code: row.code,
      model: v.model ?? '',
      api_key: v.api_key ?? '',
      base_url: v.base_url ?? '',
      avatar: v.avatar ?? '',
      system_prompt: v.system_prompt ?? ''
    })
    dialogVisible.value = true
  }

  const onSave = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
      if (!valid) return
      saving.value = true
      try {
        await ConfigService.providerSave({
          group: 'ai',
          code: form.code,
          value: {
            model: form.model,
            api_key: form.api_key,
            base_url: form.base_url,
            avatar: form.avatar,
            system_prompt: form.system_prompt
          }
        })
        ElMessage.success('保存成功')
        dialogVisible.value = false
        await fetchList()
      } catch (e) {
        // 错误已由 http 拦截器提示
      } finally {
        saving.value = false
      }
    })
  }

  const onSetActive = async (row: ProviderItem) => {
    acting.value = row.key
    try {
      await ConfigService.providerSetActive({ group: 'ai', key: row.key })
      ElMessage.success(`已切换生效服务商: ${row.name}`)
      await fetchList()
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      acting.value = ''
    }
  }

  const onDelete = async (row: ProviderItem) => {
    try {
      await ConfigService.providerDelete({ group: 'ai', key: row.key })
      ElMessage.success('删除成功')
      await fetchList()
    } catch (e) {
      // 错误已由 http 拦截器提示
    }
  }

  const onTest = async (row: ProviderItem) => {
    testing.value = row.key
    try {
      const res = await ConfigService.testAi({ group: 'ai', key: row.key })
      if (res?.code === 0) {
        ElMessage.success(`AI连通正常${res?.data?.reply ? `：${res.data.reply}` : ''}`)
      } else {
        ElMessage.error(res?.msg || 'AI测试失败')
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      testing.value = ''
    }
  }

  // ==================== AI头像上传（通用上传接口，走生效云储存） ====================
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
      form.avatar = url
      ElMessage.success('头像已上传，保存配置后生效')
    } catch (e: any) {
      ElMessage.error(e?.message || '头像上传失败')
    } finally {
      uploadingAvatar.value = false
    }
  }

  onMounted(() => {
    fetchList()
  })
</script>

<style lang="scss" scoped>
  .ai-config {
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

    .avatar-upload {
      display: flex;
      align-items: center;
      gap: 12px;

      .avatar-actions {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;

        .el-button + .el-button {
          margin-left: 0;
        }
      }
    }
  }
</style>

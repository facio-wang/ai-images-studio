<template>
  <div class="storage-config page-container">
    <!-- 顶部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">云储存配置</h2>
        <p class="page-desc">维护云储存服务商凭证，单选设置当前生效的服务商（头像/图片/APK等上传按生效配置路由）</p>
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
        <el-table-column prop="name" label="服务商" min-width="120" />
        <el-table-column label="Bucket" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.value?.bucket || '-' }}</template>
        </el-table-column>
        <el-table-column label="Endpoint / 地域" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ row.value?.endpoint || row.value?.region || '-' }}</template>
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
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑云储存服务商配置' : '新增云储存服务商配置'" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="130px">
        <el-form-item label="服务商类型" prop="code">
          <el-select v-model="form.code" :disabled="isEdit" placeholder="选择服务商" style="width: 100%" @change="onCodeChange">
            <el-option v-for="c in codeOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>

        <!-- 华为云OBS -->
        <template v-if="form.code === 'obs'">
          <el-form-item label="AccessKey" prop="access_key">
            <el-input v-model="form.access_key" placeholder="OBS AK" clearable />
          </el-form-item>
          <el-form-item label="SecretKey" prop="secret_key">
            <el-input v-model="form.secret_key" placeholder="OBS SK" show-password clearable />
          </el-form-item>
          <el-form-item label="Endpoint" prop="endpoint">
            <el-input v-model="form.endpoint" placeholder="如 obs.cn-south-1.myhuaweicloud.com" clearable />
          </el-form-item>
          <el-form-item label="Bucket" prop="bucket">
            <el-input v-model="form.bucket" placeholder="桶名" clearable />
          </el-form-item>
          <el-form-item label="Region">
            <el-input v-model="form.region" placeholder="如 cn-south-1（可选）" clearable />
          </el-form-item>
        </template>

        <!-- 阿里云OSS -->
        <template v-else-if="form.code === 'oss'">
          <el-form-item label="AccessKeyId" prop="access_key">
            <el-input v-model="form.access_key" placeholder="AccessKeyId" clearable />
          </el-form-item>
          <el-form-item label="AccessKeySecret" prop="secret_key">
            <el-input v-model="form.secret_key" placeholder="AccessKeySecret" show-password clearable />
          </el-form-item>
          <el-form-item label="Bucket" prop="bucket">
            <el-input v-model="form.bucket" placeholder="桶名" clearable />
          </el-form-item>
          <el-form-item label="Endpoint" prop="endpoint">
            <el-input v-model="form.endpoint" placeholder="如 oss-cn-hangzhou.aliyuncs.com" clearable />
          </el-form-item>
          <el-form-item label="自定义域名">
            <el-input v-model="form.domain" placeholder="绑定的加速域名（可选）" clearable />
          </el-form-item>
          <el-alert type="warning" :closable="false" show-icon title="阿里云OSS上传SDK暂未接入，可先保存配置，启用后上传将提示不支持" />
        </template>

        <!-- 腾讯云COS -->
        <template v-else-if="form.code === 'cos'">
          <el-form-item label="SecretId" prop="access_key">
            <el-input v-model="form.access_key" placeholder="SecretId" clearable />
          </el-form-item>
          <el-form-item label="SecretKey" prop="secret_key">
            <el-input v-model="form.secret_key" placeholder="SecretKey" show-password clearable />
          </el-form-item>
          <el-form-item label="Bucket" prop="bucket">
            <el-input v-model="form.bucket" placeholder="桶名（含appid，如 demo-1250000000）" clearable />
          </el-form-item>
          <el-form-item label="Region" prop="endpoint">
            <el-input v-model="form.endpoint" placeholder="如 ap-guangzhou" clearable />
          </el-form-item>
          <el-form-item label="自定义域名">
            <el-input v-model="form.domain" placeholder="绑定的加速域名（可选）" clearable />
          </el-form-item>
          <el-alert type="warning" :closable="false" show-icon title="腾讯云COS上传SDK暂未接入，可先保存配置，启用后上传将提示不支持" />
        </template>
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

  defineOptions({ name: 'SystemStorageConfig' })

  const STORAGE_CODES = [
    { value: 'obs', label: '华为云OBS' },
    { value: 'oss', label: '阿里云OSS' },
    { value: 'cos', label: '腾讯云COS' }
  ]

  const loading = ref(false)
  const saving = ref(false)
  const testing = ref<string | ''>('')
  const acting = ref<string | ''>('')
  const list = ref<ProviderItem[]>([])

  const dialogVisible = ref(false)
  const isEdit = ref(false)
  const formRef = ref<FormInstance>()

  const emptyForm = () => ({
    code: '',
    access_key: '',
    secret_key: '',
    endpoint: '',
    bucket: '',
    region: '',
    domain: ''
  })
  const form = reactive<Record<string, any>>(emptyForm())

  const codeOptions = STORAGE_CODES

  const rules: FormRules = {
    code: [{ required: true, message: '请选择服务商类型', trigger: 'change' }],
    access_key: [{ required: true, message: '请输入访问凭证', trigger: 'blur' }],
    secret_key: [{ required: true, message: '请输入密钥', trigger: 'blur' }],
    endpoint: [{ required: true, message: '请输入Endpoint/地域', trigger: 'blur' }],
    bucket: [{ required: true, message: '请输入Bucket', trigger: 'blur' }]
  }

  const fetchList = async () => {
    loading.value = true
    try {
      const res = await ConfigService.providerList('storage')
      list.value = res?.data || []
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      loading.value = false
    }
  }

  const onAdd = () => {
    isEdit.value = false
    Object.assign(form, emptyForm())
    dialogVisible.value = true
  }

  const onEdit = (row: ProviderItem) => {
    isEdit.value = true
    const v = row.value || {}
    Object.assign(form, {
      code: row.code,
      access_key: v.access_key ?? v.access_key_id ?? '',
      secret_key: v.secret_key ?? v.access_key_secret ?? '',
      endpoint: v.endpoint ?? '',
      bucket: v.bucket ?? '',
      region: v.region ?? '',
      domain: v.domain ?? ''
    })
    dialogVisible.value = true
  }

  // 切换类型时清空差异化字段
  const onCodeChange = () => {
    Object.assign(form, { access_key: '', secret_key: '', endpoint: '', bucket: '', region: '', domain: '' })
  }

  const buildValue = (): Record<string, any> => {
    if (form.code === 'obs') {
      return {
        access_key: form.access_key,
        secret_key: form.secret_key,
        endpoint: form.endpoint,
        bucket: form.bucket,
        region: form.region
      }
    }
    if (form.code === 'oss') {
      return {
        access_key_id: form.access_key,
        access_key_secret: form.secret_key,
        bucket: form.bucket,
        endpoint: form.endpoint,
        domain: form.domain
      }
    }
    return {
      access_key: form.access_key,
      secret_key: form.secret_key,
      bucket: form.bucket,
      endpoint: form.endpoint,
      domain: form.domain
    }
  }

  const onSave = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid) => {
      if (!valid) return
      saving.value = true
      try {
        await ConfigService.providerSave({
          group: 'storage',
          code: form.code,
          value: buildValue()
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
      await ConfigService.providerSetActive({ group: 'storage', key: row.key })
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
      await ConfigService.providerDelete({ group: 'storage', key: row.key })
      ElMessage.success('删除成功')
      await fetchList()
    } catch (e) {
      // 错误已由 http 拦截器提示
    }
  }

  const onTest = async (row: ProviderItem) => {
    testing.value = row.key
    try {
      const res = await ConfigService.testStorage({ group: 'storage', code: row.code })
      if (res?.code === 0) {
        ElMessage.success(res.msg || '连接成功')
      } else {
        ElMessage.error(res?.msg || '连接失败')
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      testing.value = ''
    }
  }

  onMounted(() => {
    fetchList()
  })
</script>

<style lang="scss" scoped>
  .storage-config {
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
  }
</style>

<template>
  <div class="system-config page-container">
    <!-- 顶部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">全局系统配置中心</h2>
        <p class="page-desc">集中管理短信、邮箱与APP运行配置（云储存/AI模型已拆分为独立配置页）</p>
      </div>
      <div class="header-right">
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
      </div>
    </div>

    <!-- 分组 Tab -->
    <div class="config-wrap art-custom-card">
      <el-tabs v-model="activeTab" v-loading="loading" @tab-change="onTabChange">
        <!-- 短信 -->
        <el-tab-pane label="短信渠道" name="sms">
          <el-form label-width="120px" class="config-form">
            <el-form-item label="域名">
              <el-input v-model="smsForm.domain" placeholder="短信网关域名" clearable />
            </el-form-item>
            <el-form-item label="账号">
              <el-input v-model="smsForm.name" placeholder="短信账号" clearable />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="smsForm.pwd" placeholder="短信密码" show-password clearable />
            </el-form-item>
            <el-form-item label="签名">
              <el-input v-model="smsForm.sign" placeholder="短信签名" clearable />
            </el-form-item>
            <el-form-item label="类型">
              <el-input-number v-model="smsForm.type" :min="0" controls-position="right" />
            </el-form-item>
            <el-form-item label="测试发送">
              <el-input v-model="testPhone" placeholder="测试接收手机号" style="width: 200px; margin-right: 8px" clearable />
              <el-button type="primary" :loading="testing === 'sms'" @click="onTestSms">测试短信</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 邮箱 -->
        <el-tab-pane label="邮箱服务器" name="email">
          <el-form label-width="120px" class="config-form">
            <el-form-item label="SMTP主机">
              <el-input v-model="emailForm.host" placeholder="如 smtp.qq.com" clearable />
            </el-form-item>
            <el-form-item label="端口">
              <el-input v-model="emailForm.port" placeholder="如 465" clearable />
            </el-form-item>
            <el-form-item label="加密方式">
              <el-select v-model="emailForm.encryption" style="width: 200px">
                <el-option label="SSL" value="ssl" />
                <el-option label="TLS" value="tls" />
                <el-option label="无加密" value="none" />
              </el-select>
            </el-form-item>
            <el-form-item label="账号">
              <el-input v-model="emailForm.username" placeholder="SMTP账号" clearable />
            </el-form-item>
            <el-form-item label="发件地址">
              <el-input v-model="emailForm.address" placeholder="发件邮箱地址" clearable />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="emailForm.password" placeholder="SMTP密码/授权码" show-password clearable />
            </el-form-item>
            <el-form-item label="测试发送">
              <el-input
                v-model="testEmailAddr"
                placeholder="测试收件邮箱"
                style="width: 240px; margin-right: 8px"
                clearable
              />
              <el-button type="primary" :loading="testing === 'email'" @click="onTestEmail">测试邮件</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- APP配置 -->
        <el-tab-pane label="APP配置" name="app">
          <el-form label-width="160px" class="config-form">
            <el-form-item label="接口缓存超时(秒)">
              <el-input-number v-model="appForm.apiCacheTimeOut" :min="0" controls-position="right" />
            </el-form-item>
            <el-form-item label="订单过期时间(秒)">
              <el-input-number v-model="appForm.orderExpireTime" :min="0" controls-position="right" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <!-- 保存按钮（按当前组保存） -->
      <div class="save-bar">
        <el-button type="primary" :loading="saving" @click="onSaveCurrentGroup">保存当前配置</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Refresh } from '@element-plus/icons-vue'
  import { ConfigService } from '@/api/configApi'

  defineOptions({ name: 'SystemConfig' })

  const loading = ref(false)
  const saving = ref(false)
  const testing = ref<string | ''>('')
  const activeTab = ref('sms')

  // 测试用临时输入
  const testPhone = ref('')
  const testEmailAddr = ref('')

  // 各组表单
  const smsForm = reactive<Record<string, any>>({
    domain: '',
    name: '',
    pwd: '',
    sign: '',
    type: 1
  })
  const emailForm = reactive<Record<string, any>>({
    host: '',
    port: '465',
    encryption: 'ssl',
    username: '',
    address: '',
    password: ''
  })
  const appForm = reactive<Record<string, any>>(({
    apiCacheTimeOut: 180,
    orderExpireTime: 1800
  } as unknown) as Record<string, any>)

  // 原始分组数据（用于回填）
  let groupData: Record<string, any> = {}

  // ===== 拉取列表 =====
  async function fetchList() {
    loading.value = true
    try {
      const res = await ConfigService.getList()
      const payload = res?.data
      if (payload) {
        groupData = payload
        fillForms()
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      loading.value = false
    }
  }

  // 取某 key 的 value
  function getValue(group: string, key: string): any {
    const g = groupData[group]
    if (!g || !g.items) return null
    const item = g.items.find((it: any) => it.key === key)
    return item ? item.value : null
  }

  // 回填表单
  function fillForms() {
    const sms = getValue('sms', 'SMS_TENCENT_KEY') || {}
    Object.assign(smsForm, {
      domain: sms.domain ?? '',
      name: sms.name ?? '',
      pwd: sms.pwd ?? '',
      sign: sms.sign ?? '',
      type: sms.type ?? 1
    })

    const email = getValue('email', 'KEY_EMAIL') || {}
    Object.assign(emailForm, {
      host: email.host ?? '',
      port: String(email.port ?? '465'),
      encryption: email.encryption ?? 'ssl',
      username: email.username ?? '',
      address: email.address ?? '',
      password: email.password ?? ''
    })

    const apiCache = getValue('app', 'API_CACHE_TIME_OUT')
    appForm.apiCacheTimeOut = apiCache?.value ?? 180
    const orderExpire = getValue('app', 'ORDER_EXPIRE_TIME')
    appForm.orderExpireTime = orderExpire?.value ?? 1800
  }

  function onTabChange() {
    // 切换Tab无需额外动作，表单已全部回填
  }

  // ===== 保存当前组 =====
  async function onSaveCurrentGroup() {
    saving.value = true
    try {
      const items = buildSaveItems(activeTab.value)
      const res = await ConfigService.save({ items })
      if (res?.code === 0) {
        ElMessage.success('保存成功')
        await fetchList()
      } else {
        ElMessage.error(res?.msg || '保存失败')
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      saving.value = false
    }
  }

  // 按组构造保存项
  function buildSaveItems(group: string): { key: string; value: any }[] {
    switch (group) {
      case 'sms':
        return [{ key: 'SMS_TENCENT_KEY', value: { ...smsForm } }]
      case 'email':
        return [{ key: 'KEY_EMAIL', value: { ...emailForm } }]
      case 'app':
        return [
          { key: 'API_CACHE_TIME_OUT', value: { value: Number(appForm.apiCacheTimeOut) } },
          { key: 'ORDER_EXPIRE_TIME', value: { value: Number(appForm.orderExpireTime) } }
        ]
      default:
        return []
    }
  }

  // ===== 测试：短信 =====
  async function onTestSms() {
    if (!testPhone.value) {
      ElMessage.warning('请输入测试接收手机号')
      return
    }
    // 先保存再测试，确保用最新凭证
    await onSaveCurrentGroup()
    testing.value = 'sms'
    try {
      const res = await ConfigService.testSms(testPhone.value)
      if (res?.code === 0) {
        ElMessage.success(res.msg || '短信发送成功')
      } else {
        ElMessage.error(res?.msg || '短信测试失败')
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      testing.value = ''
    }
  }

  // ===== 测试：邮件 =====
  async function onTestEmail() {
    if (!testEmailAddr.value) {
      ElMessage.warning('请输入测试收件邮箱')
      return
    }
    await onSaveCurrentGroup()
    testing.value = 'email'
    try {
      const res = await ConfigService.testEmail(testEmailAddr.value)
      if (res?.code === 0) {
        ElMessage.success(res.msg || '邮件发送成功')
      } else {
        ElMessage.error(res?.msg || '邮件测试失败')
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
  .system-config {
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

    .config-wrap {
      padding: 16px;
      border-radius: 8px;

      .config-form {
        max-width: 640px;
        margin-top: 8px;
      }

      .save-bar {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--el-border-color-lighter);
        text-align: right;
      }
    }
  }
</style>

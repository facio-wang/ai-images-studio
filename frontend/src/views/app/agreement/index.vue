<template>
  <div class="agreement-manage page-container">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">协议管理</h2>
        <p class="page-desc">维护APP内展示的用户协议与隐私政策，保存后立即对客户端生效</p>
      </div>
    </div>

    <div class="editor-card art-custom-card">
      <el-tabs v-model="activeType" @tab-change="loadDetail">
        <el-tab-pane label="用户协议" name="user" />
        <el-tab-pane label="隐私政策" name="privacy" />
      </el-tabs>

      <el-input
        v-model="title"
        class="title-input"
        placeholder="协议标题"
        maxlength="50"
      >
        <template #prepend>标题</template>
      </el-input>

      <el-input
        v-model="content"
        type="textarea"
        :rows="22"
        class="content-input"
        placeholder="协议内容：支持纯文本，段落之间空一行；保存后APP端立即展示最新内容"
      />

      <div class="save-bar">
        <span class="updated-text">最近更新：{{ updatedAt || '尚未保存过' }}</span>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import { AgreementService, type AgreementData } from '@/api/agreementApi'

  defineOptions({ name: 'Agreement' })

  const activeType = ref<'user' | 'privacy'>('user')
  const title = ref('')
  const content = ref('')
  const updatedAt = ref('')
  const loading = ref(false)
  const saving = ref(false)

  async function loadDetail() {
    loading.value = true
    try {
      const res = await AgreementService.detail(activeType.value)
      if (res?.code === 0 && res.data) {
        const d: AgreementData = res.data
        title.value = d.title || ''
        content.value = d.content || ''
        updatedAt.value = d.updated_at || ''
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      loading.value = false
    }
  }

  async function onSave() {
    if (!content.value.trim()) {
      ElMessage.warning('协议内容不能为空')
      return
    }
    saving.value = true
    try {
      const res = await AgreementService.save({
        type: activeType.value,
        title: title.value,
        content: content.value
      })
      if (res?.code === 0) {
        ElMessage.success('保存成功，APP端已生效')
        loadDetail()
      } else {
        ElMessage.error(res?.msg || '保存失败')
      }
    } catch (e) {
      // 错误已由 http 拦截器提示
    } finally {
      saving.value = false
    }
  }

  onMounted(() => {
    loadDetail()
  })
</script>

<style lang="scss" scoped>
  .agreement-manage {
    padding: 16px;

    .page-header {
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

    .editor-card {
      padding: 16px;
      border-radius: 8px;

      .title-input {
        margin-bottom: 12px;
      }

      .content-input {
        :deep(textarea) {
          font-family: 'JetBrains Mono', Consolas, monospace;
          line-height: 1.7;
        }
      }

      .save-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;

        .updated-text {
          font-size: 13px;
          color: var(--art-gray-text-800);
        }
      }
    }
  }
</style>

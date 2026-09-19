<template>
  <div class="welcome-page art-custom-card">
    <h1 class="welcome-title">Personal AI 管理后台</h1>
    <p class="welcome-desc">模板清理完成，等待业务模块接入。</p>
  </div>
</template>

<script setup lang="ts">
  defineOptions({ name: 'Home' })
</script>

<style lang="scss" scoped>
  .welcome-page {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 120px);
    text-align: center;

    .welcome-title {
      margin-bottom: 12px;
      font-size: 28px;
      font-weight: 600;
    }

    .welcome-desc {
      color: var(--art-gray-text-800);
    }
  }
</style>

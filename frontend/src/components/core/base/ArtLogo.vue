<!-- System logo component -->
<template>
  <div class="art-logo">
    <img :style="logoStyle" src="@imgs/common/capybara.png" alt="logo" />
  </div>
</template>

<script setup lang="ts">
  const props = defineProps({
    width: {
      type: Number,
      default: 36
    }
  })

  const logoStyle = computed(() => ({ width: `${props.width}px` }))
</script>

<style lang="scss" scoped>
  .art-logo {
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      width: 100%;
      height: 100%;
      /* 白底插画裁圆 + 细边框：暗色侧栏上呈现为圆形头像徽标 */
      border-radius: 50%;
      object-fit: cover;
      box-shadow: 0 0 0 1px var(--art-border-dashed-color);
    }
  }
</style>

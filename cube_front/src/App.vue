<template>
  <!-- router-view 会根据当前 URL 渲染对应的组件（如 HomeView） -->
  <router-view />
</template>

<script setup>
// 这里不需要写额外逻辑，只要保证有 router-view 即可
</script>

<style>
/* 清除默认边距，让导航栏撑满 */
body {
  margin: 0;
  padding: 0;
}
</style>
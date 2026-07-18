<template>
  <div class="common-layout">
    <el-container>
      <el-header>
        <TopHeader />
      </el-header>

      <el-main>
        <router-view />
      </el-main>

      <el-footer>
        <Footer />
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import TopHeader from '@/components/Header.vue'
import Footer from '@/components/Footer.vue'
</script>

<style>
/* 限制主内容区域的最大宽度，避免大屏下太分散 */
.el-main {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>
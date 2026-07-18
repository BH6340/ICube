<script setup>
import {ref} from 'vue'

const banners = ref([])

// 动态导入所有 banner 图片
const bannerModules = import.meta.glob('@/assets/banners/banner*.png', {eager: true})

banners.value = Object.keys(bannerModules).map(path => ({
  url: bannerModules[path].default,
  name: path.split('/').pop().replace('.png', '')
}))
</script>

<template>
  <div class="main-content">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-carousel height="300px" border-radius="8px">
          <el-carousel-item v-for="(banner, index) in banners" :key="index">
            <img :src="banner.url" class="carousel-image" :alt="banner.name">
          </el-carousel-item>
        </el-carousel>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 40px;">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>🎓 层先法教程</span>
          </template>
          <p>从零开始学习三阶魔方复原，掌握层先法。</p>
          <el-button type="primary" plain>开始学习</el-button>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>⚡ CFOP教程</span>
          </template>
          <p>学习CFOP，提升复原速度至专业水平。</p>
          <el-button type="primary" plain>开始学习</el-button>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>🏆 桥式教程</span>
          </template>
          <p>精通桥式思维，减少步数轻松超越极限。</p>
          <el-button type="primary" plain>开始学习</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.main-content {
  padding: 20px 0;
}

.carousel-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
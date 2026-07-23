<template>
  <!-- 首页主内容组件 -->
  <!-- 使用 Element Plus 的栅格系统 (el-row/el-col) 实现响应式布局 -->
  <div class="main-content">
    <!-- 轮播图区域 -->
    <!-- 使用 el-carousel 组件展示首页横幅图片 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-carousel height="300px" border-radius="8px" indicator-position="bottom">
          <el-carousel-item v-for="(banner, index) in banners" :key="index">
            <img :src="banner.url" class="carousel-image" :alt="banner.name">
          </el-carousel-item>
        </el-carousel>
      </el-col>
    </el-row>

    <!-- 热门帖子和精选公式区域 -->
    <!-- 左右两列布局，分别展示热门帖子和精选公式 -->
    <el-row :gutter="20" style="margin-top: 30px;">
      <!-- 热门帖子列 -->
      <el-col :span="12">
        <el-card class="section-card" shadow="hover">
          <template #header>
            <div class="section-header">
              <span class="section-icon">📢</span>
              <span class="section-title">热门帖子</span>
              <el-button type="text" size="small" @click="router.push('/forum')">查看更多 →</el-button>
            </div>
          </template>
          <!-- 加载骨架屏 -->
          <el-skeleton v-if="loadingPosts" :rows="5" animated />
          <div v-else class="post-list">
            <!-- 空状态 -->
            <div v-if="hotPosts.length === 0" class="empty-state">
              <p>暂无帖子</p>
            </div>
            <!-- 帖子列表 -->
            <div v-for="post in hotPosts" :key="post.id" class="post-item" @click="goToPost(post.id)">
              <div class="post-content">
                <h4 class="post-title">{{ post.title }}</h4>
                <p class="post-meta">
                  <span class="post-author">{{ post.author?.username || '未知用户' }}</span>
                  <span class="post-time">{{ new Date(post.created_at).toLocaleDateString() }}</span>
                </p>
              </div>
              <div class="post-stats">
                <span class="stat-item">👍 {{ post.like_count || 0 }}</span>
              <span class="stat-item">💬 {{ post.comment_count || 0 }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 精选公式列 -->
      <el-col :span="12">
        <el-card class="section-card" shadow="hover">
          <template #header>
            <div class="section-header">
              <span class="section-icon">✨</span>
              <span class="section-title">精选公式</span>
              <el-button type="text" size="small" @click="router.push('/formulas')">查看更多 →</el-button>
            </div>
          </template>
          <!-- 加载骨架屏 -->
          <el-skeleton v-if="loadingFormulas" :rows="5" animated />
          <div v-else class="formula-list">
            <!-- 空状态 -->
            <div v-if="hotFormulas.length === 0" class="empty-state">
              <p>暂无公式</p>
            </div>
            <!-- 公式列表 -->
            <div v-for="formula in hotFormulas" :key="formula.id" class="formula-item" @click="goToFormula(formula.id)">
              <div class="formula-content">
                <h4 class="formula-name">{{ formula.name }}</h4>
                <p class="formula-category">{{ formula.category?.name || '未分类' }}</p>
              </div>
              <div class="formula-stats">
                <span class="stat-item">👁️ {{ formula.view_count || 0 }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 魔方教程区域 -->
    <!-- 三列布局，展示层先法、CFOP、桥式三种教程入口 -->
    <el-row :gutter="20" style="margin-top: 30px;">
      <el-col :span="24">
        <el-card class="section-card" shadow="hover">
          <template #header>
            <div class="section-header">
              <span class="section-icon">🎓</span>
              <span class="section-title">魔方教程</span>
            </div>
          </template>
          <el-row :gutter="20">
            <!-- 层先法教程 -->
            <el-col :span="8">
              <div class="tutorial-card" @click="goToBeginnerTutorial">
                <div class="tutorial-icon">📚</div>
                <div class="tutorial-info">
                  <h4>层先法教程</h4>
                  <p>从零开始学习三阶魔方复原，掌握层先法。</p>
                </div>
                <el-button type="primary" plain size="small">开始学习</el-button>
              </div>
            </el-col>
            <!-- CFOP教程 -->
            <el-col :span="8">
              <div class="tutorial-card" @click="goToTutorial('cfop')">
                <div class="tutorial-icon">⚡</div>
                <div class="tutorial-info">
                  <h4>CFOP教程</h4>
                  <p>学习CFOP，提升复原速度至专业水平。</p>
                </div>
                <el-button type="primary" plain size="small">开始学习</el-button>
              </div>
            </el-col>
            <!-- 桥式教程（即将推出） -->
            <el-col :span="8">
              <div class="tutorial-card" @click="goToTutorial('roux')">
                <div class="tutorial-icon">🏆</div>
                <div class="tutorial-info">
                  <h4>桥式教程</h4>
                  <p>精通桥式思维，减少步数轻松超越极限。</p>
                </div>
                <el-button type="primary" plain size="small">开始学习</el-button>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 公式分类区域 -->
    <!-- 展示公式库的分类标签，点击可跳转 -->
    <el-row :gutter="20" style="margin-top: 30px;">
      <el-col :span="24">
        <el-card class="section-card" shadow="hover">
          <template #header>
            <div class="section-header">
              <span class="section-icon">🔥</span>
              <span class="section-title">公式分类</span>
            </div>
          </template>
          <!-- 加载骨架屏 -->
          <el-skeleton v-if="loadingCategories" :rows="1" animated />
          <div v-else class="category-list">
            <el-tag
              v-for="cat in formulaCategories"
              :key="cat.id"
              class="category-tag"
              @click="goToFormulaList(cat.name)"
            >
              {{ cat.name }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
/**
 * Main.vue - 首页主内容组件
 * 
 * 核心职责：
 * 1. 展示轮播图（自动扫描 assets/banners 目录下的图片）
 * 2. 展示热门帖子（按浏览量排序，最近30天的数据）
 * 3. 展示精选公式（按浏览量排序）
 * 4. 展示魔方教程入口（层先法、CFOP、桥式）
 * 5. 展示公式分类标签（可点击跳转）
 * 
 * 设计要点：
 * - 使用 import.meta.glob 动态导入轮播图，支持自动扫描
 * - 多个数据接口并行加载，提升首屏渲染速度
 * - 使用骨架屏优化加载体验
 * - 响应式布局，适配不同屏幕尺寸
 */

import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getPosts } from '@/api/posts'                    // 获取帖子 API
import { getFormulaList, getFormulaCategories } from '@/api/formula'  // 公式相关 API

const router = useRouter()

// 响应式状态
const banners = ref([])              // 轮播图数据
const hotPosts = ref([])             // 热门帖子列表
const hotFormulas = ref([])          // 精选公式列表
const formulaCategories = ref([])    // 公式分类列表
const loadingPosts = ref(false)      // 帖子加载状态
const loadingFormulas = ref(false)   // 公式加载状态
const loadingCategories = ref(false) // 分类加载状态

/**
 * 动态导入轮播图
 * 使用 Vite 的 import.meta.glob 特性，自动扫描 assets/banners 目录下的图片
 * 支持热更新，新增图片无需修改代码
 */
const bannerModules = import.meta.glob('@/assets/banners/banner*.png', { eager: true })

// 将导入的模块转换为轮播图数据格式
banners.value = Object.keys(bannerModules).map(path => ({
  url: bannerModules[path].default,
  name: path.split('/').pop().replace('.png', '')
}))

/**
 * 加载热门帖子
 * 
 * 逻辑：
 * 1. 查询最近30天的帖子
 * 2. 按浏览量降序排序
 * 3. 只取前5条数据
 */
const loadHotPosts = async () => {
  loadingPosts.value = true
  try {
    const oneMonthAgo = new Date()
    oneMonthAgo.setDate(oneMonthAgo.getDate() - 30)
    const dateStr = oneMonthAgo.toISOString().split('T')[0]
    const res = await getPosts({ page_size: 5, ordering: '-view_count', created_at__gte: dateStr })
    if (res.code === 100) {
      hotPosts.value = res.data.results || []
    }
  } catch (error) {
    console.error('加载热门帖子失败', error)
  } finally {
    loadingPosts.value = false
  }
}

/**
 * 加载精选公式
 * 
 * 逻辑：
 * 1. 查询公式列表
 * 2. 按浏览量降序排序
 * 3. 只取前5条数据
 */
const loadHotFormulas = async () => {
  loadingFormulas.value = true
  try {
    const res = await getFormulaList({ page_size: 5, ordering: '-view_count' })
    if (res.code === 100) {
      hotFormulas.value = res.data.results || []
    }
  } catch (error) {
    console.error('加载精选公式失败', error)
  } finally {
    loadingFormulas.value = false
  }
}

/**
 * 加载公式分类
 * 
 * 逻辑：
 * 1. 查询所有公式分类
 * 2. 返回分类列表供标签展示
 */
const loadFormulaCategories = async () => {
  loadingCategories.value = true
  try {
    const res = await getFormulaCategories()
    if (res.code === 100) {
      formulaCategories.value = res.data || []
    }
  } catch (error) {
    console.error('加载公式分类失败', error)
  } finally {
    loadingCategories.value = false
  }
}

/**
 * 跳转到帖子详情页
 * 
 * @param {number} id - 帖子 ID
 */
const goToPost = (id) => {
  router.push(`/forum/post/${id}`)
}

/**
 * 跳转到公式详情页
 * 
 * @param {number} id - 公式 ID
 * 
 * 设计说明：通过 URL query 参数传递公式 ID，在公式列表页解析并打开详情弹窗
 */
const goToFormula = (id) => {
  router.push({ path: '/formulas', query: { formula_id: id } })
}

/**
 * 跳转到层先法教程页
 */
const goToBeginnerTutorial = () => {
  router.push('/tutorial/beginner')
}

/**
 * 跳转到指定教程页
 * 
 * @param {string} type - 教程类型（cfop/roux）
 * 
 * 逻辑：
 * 1. cfop：跳转到 CFOP 教程页
 * 2. roux：显示提示信息（桥式教程尚未推出）
 */
const goToTutorial = (type) => {
  if (type === 'cfop') {
    router.push('/tutorial/cfop')
  } else {
    ElMessage.info('桥式教程即将推出，敬请期待！')
  }
}

/**
 * 跳转到公式列表页（按分类筛选）
 * 
 * @param {string} categoryName - 分类名称
 * 
 * 设计说明：通过 URL query 参数传递分类名称，在公式列表页解析并筛选
 */
const goToFormulaList = (categoryName) => {
  router.push({ path: '/formulas', query: { category: categoryName } })
}

/**
 * 组件挂载时执行初始化
 * 
 * 初始化流程：
 * 1. 并行加载热门帖子、精选公式和公式分类
 * 2. 各模块独立加载，互不阻塞
 */
onMounted(() => {
  loadHotPosts()
  loadHotFormulas()
  loadFormulaCategories()
})
</script>

<style scoped>
.main-content {
  padding: 20px 0;
}

.carousel-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.section-card {
  height: 100%;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-icon {
  font-size: 18px;
  margin-right: 8px;
}

.section-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.post-list, .formula-list {
  padding-top: 10px;
}

.post-item, .formula-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.post-item:last-child, .formula-item:last-child {
  border-bottom: none;
}

.post-item:hover, .formula-item:hover {
  background-color: #fafafa;
}

.post-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 6px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-meta {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.post-author {
  margin-right: 16px;
}

.formula-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 6px 0;
}

.formula-category {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.post-stats, .formula-stats {
  display: flex;
  gap: 12px;
}

.stat-item {
  font-size: 12px;
  color: #909399;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.tutorial-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background-color: #fafafa;
  border-radius: 8px;
  transition: transform 0.2s;
}

.tutorial-card:hover {
  transform: translateY(-4px);
}

.tutorial-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.tutorial-info {
  text-align: center;
  margin-bottom: 12px;
}

.tutorial-info h4 {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px 0;
}

.tutorial-info p {
  font-size: 12px;
  color: #909399;
  margin: 0;
  line-height: 1.5;
}

.category-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 10px;
}

.category-tag {
  cursor: pointer;
  padding: 6px 16px;
  font-size: 14px;
  transition: all 0.2s;
}

.category-tag:hover {
  transform: scale(1.05);
}
</style>

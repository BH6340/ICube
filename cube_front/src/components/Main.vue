<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getPosts } from '@/api/posts'
import { getFormulaList, getFormulaCategories } from '@/api/formula'

const router = useRouter()

const banners = ref([])
const hotPosts = ref([])
const hotFormulas = ref([])
const formulaCategories = ref([])
const loadingPosts = ref(false)
const loadingFormulas = ref(false)
const loadingCategories = ref(false)

const bannerModules = import.meta.glob('@/assets/banners/banner*.png', { eager: true })

banners.value = Object.keys(bannerModules).map(path => ({
  url: bannerModules[path].default,
  name: path.split('/').pop().replace('.png', '')
}))



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

const goToPost = (id) => {
  router.push(`/forum/post/${id}`)
}

const goToFormula = (id) => {
  router.push({ path: '/formulas', query: { formula_id: id } })
}

const goToBeginnerTutorial = () => {
  router.push('/tutorial/beginner')
}

const goToTutorial = (type) => {
  if (type === 'cfop') {
    router.push('/tutorial/cfop')
  } else {
    ElMessage.info('桥式教程即将推出，敬请期待！')
  }
}

onMounted(() => {
  loadHotPosts()
  loadHotFormulas()
  loadFormulaCategories()
})
</script>

<template>
  <div class="main-content">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-carousel height="300px" border-radius="8px" indicator-position="bottom">
          <el-carousel-item v-for="(banner, index) in banners" :key="index">
            <img :src="banner.url" class="carousel-image" :alt="banner.name">
          </el-carousel-item>
        </el-carousel>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 30px;">
      <el-col :span="12">
        <el-card class="section-card" shadow="hover">
          <template #header>
            <div class="section-header">
              <span class="section-icon">📢</span>
              <span class="section-title">热门帖子</span>
              <el-button type="text" size="small" @click="router.push('/forum')">查看更多 →</el-button>
            </div>
          </template>
          <el-skeleton v-if="loadingPosts" :rows="5" animated />
          <div v-else class="post-list">
            <div v-if="hotPosts.length === 0" class="empty-state">
              <p>暂无帖子</p>
            </div>
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

      <el-col :span="12">
        <el-card class="section-card" shadow="hover">
          <template #header>
            <div class="section-header">
              <span class="section-icon">✨</span>
              <span class="section-title">精选公式</span>
              <el-button type="text" size="small" @click="router.push('/formulas')">查看更多 →</el-button>
            </div>
          </template>
          <el-skeleton v-if="loadingFormulas" :rows="5" animated />
          <div v-else class="formula-list">
            <div v-if="hotFormulas.length === 0" class="empty-state">
              <p>暂无公式</p>
            </div>
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

    <el-row :gutter="20" style="margin-top: 30px;">
      <el-col :span="24">
        <el-card class="section-card" shadow="hover">
          <template #header>
            <div class="section-header">
              <span class="section-icon">🔥</span>
              <span class="section-title">公式分类</span>
            </div>
          </template>
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

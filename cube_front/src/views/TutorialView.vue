<template>
  <div class="tutorial-nav-container">
    <div class="welcome-section">
      <h1>🧩 魔方教程导航</h1>
      <p>从零基础小白到速拧大神，选择适合你的魔方进阶之路</p>
    </div>

    <div class="category-section">
      <h2 class="category-title">🟢 常规正阶魔方</h2>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6" v-for="cube in orderCubes" :key="cube.id">
          <el-card class="cube-card" shadow="hover">
            <div class="card-icon" :style="{ backgroundColor: cube.color }">
              <span class="cube-tag">{{ cube.tag }}</span>
            </div>
            <div class="card-content">
              <h3>{{ cube.name }}</h3>
              <p>{{ cube.desc }}</p>
              <el-button type="primary" plain @click="goToDetail(cube.path)">
                开始学习
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-divider />

    <div class="category-section">
      <h2 class="category-title">🔥 三阶魔方专项进阶</h2>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8" v-for="method in methodCubes" :key="method.id">
          <el-card class="method-card" shadow="hover">
            <template #header>
              <div class="method-header">
                <span class="method-name">{{ method.name }}</span>
                <el-tag :type="method.levelType" size="small">{{ method.level }}</el-tag>
              </div>
            </template>
            <div class="method-body">
              <p class="method-desc">{{ method.desc }}</p>
              <div class="method-features">
                <span v-for="f in method.features" :key="f" class="feature-tag">
                  ✓ {{ f }}
                </span>
              </div>
              <el-button type="success" class="full-width" @click="goToDetail(method.path)">
                探索该解法
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 二阶到五阶数据
const orderCubes = ref([
  { id: 1, name: '二阶魔方 (Pocket Cube)', tag: '2x2', desc: '结构简单，纯角块组成。适合作为魔方入门或给低龄爱好者的试水之作。', color: '#409EFF', path: '/tutorials/2x2' },
  { id: 2, name: '三阶魔方 (Rubik\'s Cube)', tag: '3x3', desc: '最经典的传统魔方！所有高级玩法和高阶魔方的基石，必学经典。', color: '#67C23A', path: '/tutorials/3x3' },
  { id: 3, name: '四阶魔方 (Rubik\'s Revenge)', tag: '4x4', desc: '高阶入门。由于没有固定中心块，会产生独特的“特殊情况”降阶降速。', color: '#E6A23C', path: '/tutorials/4x4' },
  { id: 4, name: '五阶魔方 (Professor\'s Cube)', tag: '5x5', desc: '结构更为复杂。更考验观察力和降阶法的熟练度，极具挑战性。', color: '#F56C6C', path: '/tutorials/5x5' }
])

// 三阶不同玩法数据
const methodCubes = ref([
  {
    id: 1,
    name: '层先法 (LBL Method)',
    level: '零基础新手',
    levelType: 'info',
    desc: '最直观的解法，一层一层解。只需记忆少量公式（通常 3-5 个），半小时即可学会复原。',
    features: ['极低门槛', '适合纯小白', '建立空间认知'],
    path: '/tutorials/3x3/lbl'
  },
  {
    id: 2,
    name: 'CFOP 速拧高级法',
    level: '进阶/提速必备',
    levelType: 'danger',
    desc: '目前世界上最主流、世界纪录保持者都在使用的速拧解法。分为 Cross、F2L、OLL、PLL 四步。',
    features: ['公式量 119 个', '手速极快', '轻松进 20 秒'],
    path: '/tutorials/3x3/cfop'
  },
  {
    id: 3,
    name: '桥式解法 (Roux Method)',
    level: '高阶/流体流派',
    levelType: 'warning',
    desc: '极具创意的解法。通过构建两侧 1x2x3 的“桥”，最后利用中层（M层）旋转复原，公式量极少且观察极其顺畅。',
    features: ['不依赖十字', '降步观察优秀', '单手解法首选'],
    path: '/tutorials/3x3/roux'
  }
])

const goToDetail = (path) => {
  router.push(path)
}
</script>

<style scoped>
.tutorial-nav-container {
  padding: 20px 10px;
}

.welcome-section {
  text-align: center;
  margin-bottom: 40px;
}

.welcome-section h1 {
  font-size: 32px;
  color: #303133;
  margin-bottom: 10px;
}

.welcome-section p {
  color: #909399;
  font-size: 16px;
}

.category-section {
  margin-bottom: 30px;
}

.category-title {
  font-size: 22px;
  color: #303133;
  margin-bottom: 20px;
  border-left: 5px solid #409EFF;
  padding-left: 10px;
}

/* 阶数卡片样式 */
.cube-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s;
  margin-bottom: 20px;
}

.cube-card:hover {
  transform: translateY(-5px);
}

.card-icon {
  height: 100px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
}

.cube-tag {
  font-size: 28px;
  font-weight: bold;
  letter-spacing: 1px;
}

.card-content {
  padding: 15px;
  text-align: center;
}

.card-content h3 {
  margin: 10px 0;
  color: #303133;
}

.card-content p {
  font-size: 13px;
  color: #606266;
  height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  margin-bottom: 15px;
}

/* 三阶高级算法卡片样式 */
.method-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.method-card:hover {
  border-color: #67C23A;
  box-shadow: 0 4px 12px 0 rgba(0,0,0,0.1);
}

.method-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.method-name {
  font-weight: bold;
  font-size: 16px;
}

.method-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  min-height: 70px;
}

.method-features {
  margin: 15px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-tag {
  font-size: 12px;
  background-color: #f0f9eb;
  color: #67c23a;
  padding: 4px 8px;
  border-radius: 4px;
}

.full-width {
  width: 100%;
}
</style>
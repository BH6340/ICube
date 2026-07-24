<template>
  <div class="tutorial-nav-container">
    <div class="welcome-section">
      <h1>🧩 魔方教程中心</h1>
      <p>从零基础小白到速拧大神，选择适合你的魔方进阶之路</p>
    </div>

    <div class="learning-path-section">
      <h2 class="category-title">📚 推荐学习路径</h2>
      <div class="path-flow">
        <div class="flow-node active">
          <div class="node-circle">1</div>
          <div class="node-info">
            <span class="node-title">层先法入门</span>
            <span class="node-desc">7步学会还原</span>
          </div>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-node active">
          <div class="node-circle">2</div>
          <div class="node-info">
            <span class="node-title">CFOP速拧</span>
            <span class="node-desc">进阶提速必备</span>
          </div>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-node">
          <div class="node-circle">3</div>
          <div class="node-info">
            <span class="node-title">两步OLL/PLL</span>
            <span class="node-desc">16个公式快速上手</span>
          </div>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-node">
          <div class="node-circle">4</div>
          <div class="node-info">
            <span class="node-title">完整OLL/PLL</span>
            <span class="node-desc">78个公式精通</span>
          </div>
        </div>
      </div>
    </div>

    <el-divider />

    <div class="category-section">
      <h2 class="category-title">🔥 热门教程</h2>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="featured-card beginner" @click="goToDetail('/tutorial/beginner')">
            <div class="featured-icon">
              <span class="icon-text">🌱</span>
            </div>
            <div class="featured-content">
              <h3>三阶魔方入门教程</h3>
              <p>层先法7步还原，零基础小白必学</p>
              <div class="featured-tags">
                <span class="tag beginner-tag">零基础</span>
                <span class="tag formula-tag">5个公式</span>
                <span class="tag time-tag">30分钟学会</span>
              </div>
              <el-button type="primary" class="full-width">开始学习</el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="featured-card cfop" @click="goToDetail('/tutorial/cfop')">
            <div class="featured-icon">
              <span class="icon-text">⚡</span>
            </div>
            <div class="featured-content">
              <h3>CFOP速拧高级法</h3>
              <p>世界冠军使用的方法，轻松进20秒</p>
              <div class="featured-tags">
                <span class="tag advanced-tag">进阶</span>
                <span class="tag formula-tag">119个公式</span>
                <span class="tag time-tag">1-2个月精通</span>
              </div>
              <el-button type="success" class="full-width">探索解法</el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="featured-card oll" @click="goToDetail('/tutorial/oll-essentials')">
            <div class="featured-icon">
              <span class="icon-text">🎯</span>
            </div>
            <div class="featured-content">
              <h3>两步OLL基础</h3>
              <p>仅需10个公式，快速掌握顶层定向</p>
              <div class="featured-tags">
                <span class="tag intermediate-tag">中级</span>
                <span class="tag formula-tag">10个公式</span>
                <span class="tag time-tag">1周学会</span>
              </div>
              <el-button type="warning" class="full-width">学习OLL</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-divider />

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
              <div class="card-meta">
                <span class="meta-item">{{ cube.difficulty }}</span>
                <span class="meta-item">{{ cube.formulas }}</span>
              </div>
              <el-button 
                type="primary" 
                plain 
                @click="goToDetail(cube.path)"
                :disabled="!cube.available"
              >
                {{ cube.available ? '开始学习' : '开发中' }}
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-divider />

    <div class="category-section">
      <h2 class="category-title">⚔️ 三阶魔方专项进阶</h2>
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
              <div class="method-stats">
                <div class="stat-item">
                  <span class="stat-icon">📝</span>
                  <span class="stat-value">{{ method.formulas }}</span>
                  <span class="stat-label">公式数</span>
                </div>
                <div class="stat-item">
                  <span class="stat-icon">⏱️</span>
                  <span class="stat-value">{{ method.targetTime }}</span>
                  <span class="stat-label">目标时间</span>
                </div>
                <div class="stat-item">
                  <span class="stat-icon">📊</span>
                  <span class="stat-value">{{ method.difficulty }}</span>
                  <span class="stat-label">难度</span>
                </div>
              </div>
              <div class="method-features">
                <span v-for="f in method.features" :key="f" class="feature-tag">
                  ✓ {{ f }}
                </span>
              </div>
              <el-button 
                type="success" 
                class="full-width" 
                @click="goToDetail(method.path)"
                :disabled="!method.available"
              >
                {{ method.available ? '探索该解法' : '开发中' }}
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-divider />

    <div class="category-section">
      <h2 class="category-title">🎓 CFOP进阶课程</h2>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12">
          <el-card class="cfop-card oll-essentials" @click="goToDetail('/tutorial/oll-essentials')">
            <div class="cfop-card-header">
              <span class="cfop-icon">🎯</span>
              <div class="cfop-header-info">
                <h3>两步OLL基础</h3>
                <p>快速掌握顶层定向的捷径</p>
              </div>
              <el-tag type="info">初学者路径</el-tag>
            </div>
            <div class="cfop-card-body">
              <div class="cfop-stats">
                <div class="cfop-stat">
                  <span class="stat-num">10</span>
                  <span class="stat-text">个算法</span>
                </div>
                <div class="cfop-stat">
                  <span class="stat-num">3</span>
                  <span class="stat-text">种棱块情况</span>
                </div>
                <div class="cfop-stat">
                  <span class="stat-num">7</span>
                  <span class="stat-text">种角块情况</span>
                </div>
              </div>
              <p class="cfop-desc">两步OLL将完整OLL（57种情况）简化为两个步骤，适合初学者快速上手。</p>
              <el-button type="warning" @click.stop="goToDetail('/tutorial/oll-essentials')">学习两步OLL →</el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12">
          <el-card class="cfop-card pll-essentials" @click="goToDetail('/tutorial/pll-essentials')">
            <div class="cfop-card-header">
              <span class="cfop-icon">🏁</span>
              <div class="cfop-header-info">
                <h3>两步PLL基础</h3>
                <p>完成顶层排列的关键步骤</p>
              </div>
              <el-tag type="info">初学者路径</el-tag>
            </div>
            <div class="cfop-card-body">
              <div class="cfop-stats">
                <div class="cfop-stat">
                  <span class="stat-num">6</span>
                  <span class="stat-text">个算法</span>
                </div>
                <div class="cfop-stat">
                  <span class="stat-num">2</span>
                  <span class="stat-text">种角块情况</span>
                </div>
                <div class="cfop-stat">
                  <span class="stat-num">4</span>
                  <span class="stat-text">种棱块情况</span>
                </div>
              </div>
              <p class="cfop-desc">两步PLL将完整PLL（21种情况）简化为两个步骤，让你快速完成魔方复原。</p>
              <el-button type="warning" @click.stop="goToDetail('/tutorial/pll-essentials')">学习两步PLL →</el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12">
          <el-card class="cfop-card complete-oll" @click="goToDetail('/tutorial/complete-oll')">
            <div class="cfop-card-header">
              <span class="cfop-icon">🌟</span>
              <div class="cfop-header-info">
                <h3>完整OLL教程</h3>
                <p>掌握所有57种顶层定向情况</p>
              </div>
              <el-tag type="danger">进阶路径</el-tag>
            </div>
            <div class="cfop-card-body">
              <div class="cfop-stats">
                <div class="cfop-stat">
                  <span class="stat-num">57</span>
                  <span class="stat-text">个算法</span>
                </div>
                <div class="cfop-stat">
                  <span class="stat-num">4</span>
                  <span class="stat-text">大系列</span>
                </div>
                <div class="cfop-stat">
                  <span class="stat-num">2-3s</span>
                  <span class="stat-text">目标时间</span>
                </div>
              </div>
              <p class="cfop-desc">完整OLL是速拧选手的必修课，掌握后可达到sub-20秒水平。</p>
              <el-button type="danger" @click.stop="goToDetail('/tutorial/complete-oll')">学习完整OLL →</el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12">
          <el-card class="cfop-card complete-pll" @click="goToDetail('/tutorial/complete-pll')">
            <div class="cfop-card-header">
              <span class="cfop-icon">💎</span>
              <div class="cfop-header-info">
                <h3>完整PLL教程</h3>
                <p>掌握所有21种顶层排列情况</p>
              </div>
              <el-tag type="danger">进阶路径</el-tag>
            </div>
            <div class="cfop-card-body">
              <div class="cfop-stats">
                <div class="cfop-stat">
                  <span class="stat-num">21</span>
                  <span class="stat-text">个算法</span>
                </div>
                <div class="cfop-stat">
                  <span class="stat-num">3</span>
                  <span class="stat-text">大类型</span>
                </div>
                <div class="cfop-stat">
                  <span class="stat-num">2-3s</span>
                  <span class="stat-text">目标时间</span>
                </div>
              </div>
              <p class="cfop-desc">完整PLL让你一步完成顶层排列，配合完整OLL达到专业速拧水平。</p>
              <el-button type="danger" @click.stop="goToDetail('/tutorial/complete-pll')">学习完整PLL →</el-button>
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

const orderCubes = ref([
  { 
    id: 1, 
    name: '二阶魔方 (Pocket Cube)', 
    tag: '2x2', 
    desc: '结构简单，纯角块组成。适合作为魔方入门或给低龄爱好者的试水之作。', 
    color: '#409EFF', 
    path: '/tutorial/beginner',
    available: false,
    difficulty: '简单',
    formulas: '0个公式'
  },
  { 
    id: 2, 
    name: '三阶魔方 (Rubik\'s Cube)', 
    tag: '3x3', 
    desc: '最经典的传统魔方！所有高级玩法和高阶魔方的基石，必学经典。', 
    color: '#67C23A', 
    path: '/tutorial/beginner',
    available: true,
    difficulty: '入门',
    formulas: '5个公式'
  },
  { 
    id: 3, 
    name: '四阶魔方 (Rubik\'s Revenge)', 
    tag: '4x4', 
    desc: '高阶入门。由于没有固定中心块，会产生独特的"特殊情况"降阶降速。', 
    color: '#E6A23C', 
    path: '/tutorials/4x4',
    available: false,
    difficulty: '中等',
    formulas: '3个特殊公式'
  },
  { 
    id: 4, 
    name: '五阶魔方 (Professor\'s Cube)', 
    tag: '5x5', 
    desc: '结构更为复杂。更考验观察力和降阶法的熟练度，极具挑战性。', 
    color: '#F56C6C', 
    path: '/tutorials/5x5',
    available: false,
    difficulty: '较难',
    formulas: '4个特殊公式'
  }
])

const methodCubes = ref([
  {
    id: 1,
    name: '层先法 (LBL Method)',
    level: '零基础新手',
    levelType: 'info',
    desc: '最直观的解法，一层一层解。只需记忆少量公式（通常 3-5 个），半小时即可学会复原。',
    features: ['极低门槛', '适合纯小白', '建立空间认知'],
    path: '/tutorial/beginner',
    available: true,
    formulas: '5个',
    targetTime: '1-2分钟',
    difficulty: '入门'
  },
  {
    id: 2,
    name: 'CFOP 速拧高级法',
    level: '进阶/提速必备',
    levelType: 'danger',
    desc: '目前世界上最主流、世界纪录保持者都在使用的速拧解法。分为 Cross、F2L、OLL、PLL 四步。',
    features: ['公式量 119 个', '手速极快', '轻松进 20 秒'],
    path: '/tutorial/cfop',
    available: true,
    formulas: '119个',
    targetTime: 'sub-20秒',
    difficulty: '高级'
  },
  {
    id: 3,
    name: '桥式解法 (Roux Method)',
    level: '高阶/流体流派',
    levelType: 'warning',
    desc: '极具创意的解法。通过构建两侧 1x2x3 的"桥"，最后利用中层（M层）旋转复原，公式量极少且观察极其顺畅。',
    features: ['不依赖十字', '降步观察优秀', '单手解法首选'],
    path: '/tutorials/3x3/roux',
    available: false,
    formulas: '少量',
    targetTime: 'sub-25秒',
    difficulty: '高级'
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

.learning-path-section {
  margin-bottom: 40px;
}

.path-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 15px;
  padding: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
}

.flow-node {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.15);
  padding: 12px 20px;
  border-radius: 50px;
  transition: all 0.3s;
}

.flow-node.active {
  background: rgba(255, 255, 255, 0.25);
}

.node-circle {
  width: 32px;
  height: 32px;
  background: #fff;
  color: #667eea;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.node-info {
  display: flex;
  flex-direction: column;
}

.node-title {
  font-size: 14px;
  font-weight: bold;
  color: #fff;
}

.node-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.flow-arrow {
  color: rgba(255, 255, 255, 0.6);
  font-size: 20px;
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

.featured-card {
  margin-bottom: 20px;
  transition: transform 0.3s;
  cursor: pointer;
}

.featured-card:hover {
  transform: translateY(-5px);
}

.featured-card.beginner {
  border-top: 4px solid #67C23A;
}

.featured-card.cfop {
  border-top: 4px solid #F56C6C;
}

.featured-card.oll {
  border-top: 4px solid #E6A23C;
}

.featured-icon {
  text-align: center;
  padding: 20px 0;
}

.icon-text {
  font-size: 48px;
}

.featured-content {
  text-align: center;
}

.featured-content h3 {
  margin-bottom: 10px;
  font-size: 18px;
  color: #303133;
}

.featured-content p {
  font-size: 14px;
  color: #606266;
  margin-bottom: 15px;
}

.featured-tags {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.tag {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
}

.tag.beginner-tag {
  background: #e8f5e9;
  color: #2e7d32;
}

.tag.advanced-tag {
  background: #ffebee;
  color: #c62828;
}

.tag.intermediate-tag {
  background: #fff3e0;
  color: #e65100;
}

.tag.formula-tag {
  background: #e3f2fd;
  color: #1565c0;
}

.tag.time-tag {
  background: #f3e5f5;
  color: #7b1fa2;
}

.full-width {
  width: 100%;
}

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
  margin-bottom: 10px;
}

.card-meta {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 15px;
}

.meta-item {
  font-size: 12px;
  color: #909399;
  background: #f5f5f5;
  padding: 4px 10px;
  border-radius: 4px;
}

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

.method-body {
  padding: 15px 0;
}

.method-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  min-height: 70px;
}

.method-stats {
  display: flex;
  justify-content: space-around;
  margin: 15px 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-icon {
  font-size: 20px;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 12px;
  color: #909399;
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

.cfop-card {
  margin-bottom: 20px;
  transition: transform 0.3s;
  cursor: pointer;
}

.cfop-card:hover {
  transform: translateY(-3px);
}

.cfop-card-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.cfop-icon {
  font-size: 32px;
}

.cfop-header-info h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.cfop-header-info p {
  margin: 5px 0 0;
  font-size: 13px;
  color: #909399;
}

.cfop-card-body {
  padding: 15px 0;
}

.cfop-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.cfop-stat {
  flex: 1;
  text-align: center;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-num {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-text {
  font-size: 12px;
  color: #909399;
}

.cfop-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 15px;
}

.cfop-card.oll-essentials {
  border-left: 4px solid #E6A23C;
}

.cfop-card.pll-essentials {
  border-left: 4px solid #F093FB;
}

.cfop-card.complete-oll {
  border-left: 4px solid #4FACFE;
}

.cfop-card.complete-pll {
  border-left: 4px solid #43E97B;
}

@media (max-width: 768px) {
  .path-flow {
    flex-direction: column;
    padding: 20px;
  }
  
  .flow-arrow {
    transform: rotate(90deg);
  }
  
  .method-stats {
    flex-direction: column;
    gap: 10px;
  }
  
  .cfop-stats {
    flex-direction: column;
  }
}
</style>
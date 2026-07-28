<template>
  <div class="tutorial-container">
    <div class="tutorial-header">
      <h1>CFOP方法教程</h1>
      <p class="subtitle">将你的解题时间减半 - 学习世界冠军使用的方法</p>
      <el-button @click="goBack" icon="el-icon-arrow-left" plain size="small">返回首页</el-button>
    </div>

    <div class="tutorial-body">
      <div class="steps-sidebar">
        <el-steps :active="currentStep" align-center direction="vertical">
          <el-step v-for="(step, index) in steps" :key="index" :title="step.title">
            <template #description>
              <span>{{ step.subtitle }}</span>
            </template>
          </el-step>
        </el-steps>
      </div>

      <div class="steps-content">
        <transition name="fade" mode="out-in">
          <div :key="currentStep" class="step-detail">
            <div class="step-header">
              <h2>{{ steps[currentStep].title }}</h2>
              <p>{{ steps[currentStep].subtitle }}</p>
            </div>

            <div class="step-info">
              <el-row :gutter="20">
                <el-col :span="6">
                  <div class="info-card">
                    <span class="info-icon">{{ steps[currentStep].icon }}</span>
                    <span class="info-text">{{ steps[currentStep].stats.algoCount }}</span>
                    <span class="info-label">算法数</span>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="info-card">
                    <span class="info-icon">⏱️</span>
                    <span class="info-text">{{ steps[currentStep].stats.targetTime }}</span>
                    <span class="info-label">目标时间</span>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="info-card">
                    <span class="info-icon">📊</span>
                    <span class="info-text">{{ steps[currentStep].stats.difficulty }}</span>
                    <span class="info-label">难度</span>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="info-card">
                    <span class="info-icon">🎯</span>
                    <span class="info-text">{{ steps[currentStep].stats.goal }}</span>
                    <span class="info-label">目标</span>
                  </div>
                </el-col>
              </el-row>
            </div>

            <div class="step-content">
              <div v-html="steps[currentStep].content"></div>
            </div>

            <div v-if="steps[currentStep].formula && steps[currentStep].formula.length > 0" class="step-formula">
              <h3>核心公式</h3>
              <div v-for="(formula, fIndex) in steps[currentStep].formula" :key="fIndex" class="formula-group">
                <div v-if="formula.name" class="formula-name">{{ formula.name }}</div>
                <div class="formula-box">
                  <span v-for="(move, mIndex) in formula.moves" :key="mIndex" class="formula-item">{{ move }}</span>
                </div>
              </div>
            </div>

            <div v-if="steps[currentStep].tips" class="step-tips">
              <h3>练习技巧</h3>
              <ul>
                <li v-for="(tip, i) in steps[currentStep].tips" :key="i">{{ tip }}</li>
              </ul>
            </div>

            <div v-if="steps[currentStep].advanced" class="step-advanced">
              <h3>进阶学习</h3>
              <div v-html="steps[currentStep].advanced"></div>
            </div>
          </div>
        </transition>

        <div class="step-nav">
          <el-button 
            @click="prevStep" 
            :disabled="currentStep === 0" 
            icon="el-icon-arrow-left"
          >
            上一步
          </el-button>
          <el-button 
            v-if="currentStep < steps.length - 1"
            @click="nextStep" 
            type="primary" 
            icon="el-icon-arrow-right"
          >
            下一步
          </el-button>
          <el-button 
            v-else
            @click="goBack"
            type="success" 
            icon="el-icon-check"
          >
            完成学习
          </el-button>
        </div>
      </div>
    </div>

    <div class="learning-path">
      <h2>学习路径选择</h2>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="path-card beginner" @click="goToOllEssentials">
            <template #header>
              <div class="path-header">
                <span class="path-icon">🌱</span>
                <span class="path-title">初学者路径 - 两步CFOP</span>
                <span class="path-arrow">→</span>
              </div>
            </template>
            <div class="path-content">
              <ul>
                <li>✓ 仅需16个算法（相比完整CFOP的78个）</li>
                <li>✓ 1-2周内学会</li>
                <li>✓ 立即达到sub-30秒</li>
                <li>✓ 平滑过渡到完整CFOP</li>
              </ul>
              <div class="path-algorithms">
                <span class="alg-item">两步OLL: 10个</span>
                <span class="alg-item">两步PLL: 6个</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="path-card advanced" @click="goToCompleteOLL">
            <template #header>
              <div class="path-header">
                <span class="path-icon">⚡</span>
                <span class="path-title">进阶路径 - 完整CFOP</span>
                <span class="path-arrow">→</span>
              </div>
            </template>
            <div class="path-content">
              <ul>
                <li>✓ 完整OLL（57种情况）</li>
                <li>✓ 完整PLL（21种情况）</li>
                <li>✓ 达到sub-20秒</li>
                <li>✓ 掌握所有高级技巧</li>
              </ul>
              <div class="path-algorithms">
                <span class="alg-item">OLL: 57个</span>
                <span class="alg-item">PLL: 21个</span>
                <span class="alg-item">F2L: 41个</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
/**
 * CFOPTutorial.vue - CFOP 进阶教程页面
 *
 * 核心职责：
 * 1. 展示 CFOP 方法的分步学习内容
 * 2. 提供步骤导航和进度显示
 * 3. 每个步骤包含算法数量、目标时间等统计信息
 *
 * 功能特性：
 *   - 步骤式引导，currentStep 追踪当前学习步骤
 *   - 每步骤展示标题、副标题、图标和统计信息
 *   - 支持跳转到具体公式页面
 *
 * 设计要点：
 *   - steps 数组存储各步骤的详细内容
 *   - 点击步骤跳转到 PLL/OLL/F2L 等具体教程
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentStep = ref(0)

const steps = [
  {
    title: '第一步：十字 (Cross)',
    subtitle: '高效规划和执行底层十字',
    icon: '🔲',
    stats: {
      algoCount: '0个',
      targetTime: '3-5秒',
      difficulty: '简单',
      goal: '8步以内完成'
    },
    content: `
      <p>十字是CFOP的第一步，也是最容易被忽视的一步。目标是在底层完成一个十字，同时规划你的下一个F2L对。</p>
      <h4>十字规划技巧：</h4>
      <ol>
        <li><strong>观察阶段：</strong>在15秒观察期间，找到4个白色棱块的位置</li>
        <li><strong>选择最佳面：</strong>选择需要最少步数的面开始</li>
        <li><strong>高效执行：</strong>目标是8步或更少完成十字</li>
        <li><strong>提前规划：</strong>在完成十字的同时，寻找第一个F2L配对</li>
      </ol>
      <p><strong>关键原则：</strong>十字不需要算法，但需要大量练习来提高规划效率。一个好的十字可以为整个解法节省2-3秒。</p>
    `,
    formula: [
      { name: '示例十字公式', moves: ['F', 'R', 'D', 'R\'', 'U\'', 'R'] }
    ],
    tips: [
      '练习盲拧十字，不看魔方完成十字',
      '学习十字规划技巧，目标8步以内',
      '在观察期间就开始规划十字',
      '完成十字后立即寻找第一个F2L对'
    ],
    advanced: `
      <p><strong>高级技巧：</strong></p>
      <ul>
        <li><strong>自由十字：</strong>不局限于某一面，选择最优的起始面</li>
        <li><strong>预判十字：</strong>在完成十字时，同时观察第一个F2L配对</li>
        <li><strong>速拧技巧：</strong>学习高效的指法，减少换手次数</li>
      </ul>
    `
  },
  {
    title: '第二步：F2L (First Two Layers)',
    subtitle: '配对并插入角块-棱块对',
    icon: '🤝',
    stats: {
      algoCount: '41个',
      targetTime: '10-12秒',
      difficulty: '中等',
      goal: '直觉配对'
    },
    content: `
      <p>F2L是CFOP中最重要的一步，它将前两层同时解决。通过将角块和棱块配对，然后插入相应位置。</p>
      <h4>F2L基本概念：</h4>
      <ol>
        <li><strong>配对：</strong>找到一个角块和对应的棱块，将它们配对</li>
        <li><strong>插入：</strong>将配对好的角块-棱块对插入前两层</li>
        <li><strong>4对完成：</strong>需要完成4个F2L配对</li>
      </ol>
      <p><strong>学习路径：</strong>建议先从直觉F2L开始，掌握配对技巧后再学习算法。</p>
    `,
    formula: [
      { name: '基本F2L插入', moves: ['U', 'R', 'U\'', 'R\''] },
      { name: '反方向插入', moves: ['U\'', 'L\'', 'U', 'L'] },
      { name: '角块在顶层', moves: ['R', 'U', 'R\'', 'U', 'R', 'U\'', 'R\''] },
      { name: '棱块在顶层', moves: ['U\'', 'R', 'U', 'R\'', 'U', 'R', 'U\'', 'R\''] }
    ],
    tips: [
      '先学习直觉F2L，不要急于背公式',
      '练习预判，在完成当前配对时寻找下一个',
      '尽量减少转体，学习用左手解决左边的配对',
      '熟悉41种F2L情况，但不需要全部记住'
    ],
    advanced: `
      <p><strong>进阶技巧：</strong></p>
      <ul>
        <li><strong>空槽技巧：</strong>利用已完成的槽位来调整配对</li>
        <li><strong>双F2L：</strong>同时处理两个配对</li>
        <li><strong>预判：</strong>在观察期间定位前两个F2L配对</li>
        <li><strong>指法优化：</strong>学习高效的F2L指法</li>
      </ul>
    `
  },
  {
    title: '第三步：OLL (Orientation of Last Layer)',
    subtitle: '一步定向整个顶层',
    icon: '🎯',
    stats: {
      algoCount: '57个(两步10个)',
      targetTime: '2-3秒',
      difficulty: '中等',
      goal: '识别所有情况'
    },
    content: `
      <p>OLL是CFOP的第三步，目标是将顶层所有块的黄色面朝上。完整OLL有57种情况，但初学者可以从两步OLL开始。</p>
      <h4>两步OLL（适合初学者）：</h4>
      <ol>
        <li><strong>第一步：调整棱块方向（3种情况）</strong>
          <ul>
            <li>点：F R U R' U' F'</li>
            <li>小拐弯：F R U R' U' F'</li>
            <li>一字：F R U R' U' F'</li>
          </ul>
        </li>
        <li><strong>第二步：调整角块方向（7种情况）</strong>
          <ul>
            <li>Sune：R U R' U R U2 R'</li>
            <li>Anti-Sune：R' U' R U' R' U2 R</li>
            <li>其他5种情况</li>
          </ul>
        </li>
      </ol>
      <p><strong>学习建议：</strong>先学习两步OLL（10个算法），达到sub-30秒后再学习完整OLL（57个算法）。</p>
    `,
    formula: [
      { name: 'Sune', moves: ['R', 'U', 'R\'', 'U', 'R', 'U2', 'R\''] },
      { name: 'Anti-Sune', moves: ['R\'', 'U\'', 'R', 'U\'', 'R\'', 'U2', 'R'] },
      { name: '十字公式', moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\''] },
      { name: 'T-case', moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'f', 'R', 'U', 'R\'', 'U\'', 'f\''] },
      { name: 'L-case', moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R', 'U\'', 'R\'', 'U', 'R'] }
    ],
    tips: [
      '先学习两步OLL，再逐步过渡到完整OLL',
      '练习OLL识别，目标0.5秒内识别情况',
      '学习多个公式变体，选择适合自己的',
      '练习OLL预判，在F2L最后一步就识别OLL情况'
    ],
    advanced: `
      <p><strong>完整OLL学习建议：</strong></p>
      <ul>
        <li><strong>分组学习：</strong>按形状分组（T、L、S、Pi等）</li>
        <li><strong>公式优化：</strong>学习最短、最高效的公式</li>
        <li><strong>指法练习：</strong>每个公式都要练习到流畅</li>
        <li><strong>视觉识别：</strong>培养快速识别OLL情况的能力</li>
      </ul>
    `
  },
  {
    title: '第四步：PLL (Permutation of Last Layer)',
    subtitle: '排列顶层块完成魔方',
    icon: '🏁',
    stats: {
      algoCount: '21个(两步6个)',
      targetTime: '2-3秒',
      difficulty: '中等',
      goal: '快速完成排列'
    },
    content: `
      <p>PLL是CFOP的最后一步，目标是将顶层所有块排列到正确位置。完整PLL有21种情况，但初学者可以从两步PLL开始。</p>
      <h4>两步PLL（适合初学者）：</h4>
      <ol>
        <li><strong>第一步：排列角块（2种情况）</strong>
          <ul>
            <li>A-perm（顺时针）</li>
            <li>A-perm（逆时针）</li>
          </ul>
        </li>
        <li><strong>第二步：排列棱块（4种情况）</strong>
          <ul>
            <li>U-perm（顺时针）</li>
            <li>U-perm（逆时针）</li>
            <li>H-perm</li>
            <li>Z-perm</li>
          </ul>
        </li>
      </ol>
      <p><strong>学习建议：</strong>先学习两步PLL（6个算法），达到sub-30秒后再学习完整PLL（21个算法）。</p>
    `,
    formula: [
      { name: 'U-perm (顺时针)', moves: ['M2', 'U', 'M2', 'U2', 'M2', 'U', 'M2'] },
      { name: 'U-perm (逆时针)', moves: ['M2', 'U\'', 'M2', 'U2', 'M2', 'U\'', 'M2'] },
      { name: 'A-perm (顺时针)', moves: ['R', 'U', 'R\'', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R\'', 'F', 'R2', 'U\'', 'R\'', 'U\''] },
      { name: 'A-perm (逆时针)', moves: ['R\'', 'U\'', 'R', 'F', 'R\'', 'U\'', 'R', 'U', 'R', 'F\'', 'R2', 'U', 'R', 'U'] },
      { name: 'H-perm', moves: ['M2', 'U2', 'M2', 'U2', 'M2'] },
      { name: 'Z-perm', moves: ['M', 'U', 'M2', 'U', 'M2', 'U', 'M'] }
    ],
    tips: [
      '先学习两步PLL，再逐步过渡到完整PLL',
      '练习PLL识别，目标0.5秒内识别情况',
      '学习多个公式变体，选择适合自己的',
      '练习PLL预判，在OLL完成前就识别PLL情况'
    ],
    advanced: `
      <p><strong>完整PLL学习建议：</strong></p>
      <ul>
        <li><strong>分组学习：</strong>按类型分组（Corner、Edge、Corner+Edge）</li>
        <li><strong>公式优化：</strong>学习最短、最高效的公式</li>
        <li><strong>指法练习：</strong>每个公式都要练习到流畅</li>
        <li><strong>视觉识别：</strong>培养快速识别PLL情况的能力</li>
      </ul>
    `
  }
]

const nextStep = () => {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const goBack = () => {
  router.push('/tutorials')
}

const goToOllEssentials = () => {
  router.push('/tutorial/oll-essentials')
}

const goToCompleteOLL = () => {
  router.push('/tutorial/complete-oll')
}
</script>

<style scoped>
.tutorial-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.tutorial-header {
  text-align: center;
  margin-bottom: 30px;
}

.tutorial-header h1 {
  font-size: 32px;
  color: #333;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 18px;
  color: #666;
  margin-bottom: 15px;
}

.tutorial-body {
  display: flex;
  gap: 30px;
}

.steps-sidebar {
  flex-shrink: 0;
  width: 280px;
}

.steps-content {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.step-header h2 {
  font-size: 24px;
  color: #333;
  margin-bottom: 5px;
}

.step-header p {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
}

.step-info {
  margin-bottom: 20px;
}

.info-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
}

.info-icon {
  font-size: 24px;
  margin-bottom: 8px;
  display: block;
}

.info-text {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  display: block;
}

.info-label {
  font-size: 12px;
  color: #666;
}

.step-content {
  margin-bottom: 20px;
}

.step-content p {
  font-size: 15px;
  line-height: 1.8;
  color: #444;
  margin-bottom: 10px;
}

.step-content h4 {
  font-size: 16px;
  color: #333;
  margin: 15px 0 10px;
}

.step-content ol,
.step-content ul {
  padding-left: 20px;
  margin-bottom: 15px;
}

.step-content li {
  font-size: 15px;
  line-height: 1.8;
  color: #444;
  margin-bottom: 5px;
}

.step-formula {
  background: #e8f5e9;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.step-formula h3 {
  font-size: 16px;
  color: #2e7d32;
  margin-bottom: 15px;
}

.formula-group {
  margin-bottom: 15px;
}

.formula-group:last-child {
  margin-bottom: 0;
}

.formula-name {
  font-size: 14px;
  color: #1b5e20;
  margin-bottom: 8px;
  font-weight: bold;
}

.formula-box {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.formula-item {
  display: inline-block;
  background: #4caf50;
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: bold;
}

.step-tips {
  background: #fff3e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.step-tips h3 {
  font-size: 16px;
  color: #e65100;
  margin-bottom: 15px;
}

.step-tips ul {
  padding-left: 20px;
}

.step-tips li {
  font-size: 14px;
  line-height: 1.8;
  color: #5d4037;
  margin-bottom: 8px;
  list-style-type: disc;
}

.step-advanced {
  background: #e3f2fd;
  border-radius: 8px;
  padding: 20px;
}

.step-advanced h3 {
  font-size: 16px;
  color: #1565c0;
  margin-bottom: 15px;
}

.step-advanced p {
  font-size: 14px;
  line-height: 1.8;
  color: #1565c0;
  margin-bottom: 10px;
}

.step-advanced ul {
  padding-left: 20px;
}

.step-advanced li {
  font-size: 14px;
  line-height: 1.8;
  color: #0d47a1;
  margin-bottom: 8px;
}

.step-nav {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.learning-path {
  margin-top: 30px;
}

.learning-path h2 {
  font-size: 24px;
  color: #333;
  text-align: center;
  margin-bottom: 20px;
}

.path-card {
  transition: transform 0.3s ease;
  cursor: pointer;
}

.path-card:hover {
  transform: translateY(-5px);
}

.path-header {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: space-between;
}

.path-arrow {
  color: #999;
  font-size: 16px;
  transition: color 0.3s ease;
}

.path-card:hover .path-arrow {
  color: #4caf50;
}

.path-card.advanced:hover .path-arrow {
  color: #ff9800;
}

.path-icon {
  font-size: 24px;
}

.path-title {
  font-size: 16px;
  font-weight: bold;
}

.path-card.beginner .path-title {
  color: #4caf50;
}

.path-card.advanced .path-title {
  color: #ff9800;
}

.path-content ul {
  padding-left: 20px;
  margin: 15px 0;
}

.path-content li {
  font-size: 14px;
  line-height: 1.8;
  color: #444;
  margin-bottom: 5px;
}

.path-algorithms {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 15px;
}

.alg-item {
  background: #e0e0e0;
  padding: 5px 12px;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 900px) {
  .tutorial-body {
    flex-direction: column;
  }

  .steps-sidebar {
    width: 100%;
  }

  .steps-sidebar .el-steps {
    direction: horizontal;
  }

  .learning-path .el-col {
    span: 24;
  }
}
</style>
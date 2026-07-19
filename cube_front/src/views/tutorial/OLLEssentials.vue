<template>
  <div class="oll-essentials">
    <div class="page-header">
      <div class="header-content">
        <h1>OLL基础</h1>
        <p>两步完成顶层定向 - 仅需10个算法</p>
        <div class="header-tags">
          <span class="tag beginner">初学者路径</span>
          <span class="tag algorithm-count">10个算法</span>
        </div>
      </div>
      <div class="progress-bar">
        <div class="progress-info">
          <span>学习进度</span>
          <span>{{ progress }}%</span>
        </div>
        <el-progress :percentage="progress" :stroke-width="6" />
      </div>
    </div>

    <div class="nav-tabs">
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="两步OLL概览" name="overview">
          <div class="overview-content">
            <div class="overview-card">
              <h3>什么是两步OLL？</h3>
              <p>两步OLL是CFOP初学者的最佳起点。它将完整OLL（57种情况）简化为两个步骤，只需学习10个算法就能解决所有顶层定向问题。</p>
            </div>
            <div class="step-flow">
              <div class="flow-step">
                <div class="flow-icon">1</div>
                <div class="flow-content">
                  <h4>第一步：棱块定向</h4>
                  <p>将顶层4个棱块调整为黄色面朝上，共有3种情况</p>
                </div>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <div class="flow-icon">2</div>
                <div class="flow-content">
                  <h4>第二步：角块定向</h4>
                  <p>将顶层4个角块调整为黄色面朝上，共有7种情况</p>
                </div>
              </div>
            </div>
            <div class="tips-card">
              <h4>💡 学习建议</h4>
              <ul>
                <li>先熟练掌握两步OLL，达到sub-30秒后再学习完整OLL</li>
                <li>每天练习10-15分钟，重点是快速识别情况</li>
                <li>练习预判：在F2L最后一步就开始观察OLL情况</li>
              </ul>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="第一步：棱块定向" name="edge">
          <div class="cases-container">
            <div class="case-card" v-for="(caseItem, index) in edgeCases" :key="index">
              <div class="case-header">
                <span class="case-name">{{ caseItem.name }}</span>
                <span class="case-difficulty">{{ caseItem.difficulty }}</span>
              </div>
              <div class="case-visual">
                <div class="cube-preview">
                  <div class="yellow-faces">
                    <div v-for="pos in caseItem.yellowPositions" :key="pos" class="yellow-face" :class="pos"></div>
                  </div>
                </div>
                <div class="case-stats">
                  <span>步数: {{ caseItem.moves.length }}</span>
                  <span>难度: {{ caseItem.difficulty }}</span>
                </div>
              </div>
              <div class="case-formula">
                <div class="formula-display">
                  <span v-for="(move, mIndex) in caseItem.moves" :key="mIndex" class="move-item">{{ move }}</span>
                </div>
                <div class="formula-name">{{ caseItem.formulaName }}</div>
              </div>
              <div class="case-tips">
                <p>{{ caseItem.tips }}</p>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="第二步：角块定向" name="corner">
          <div class="cases-container">
            <div class="case-card" v-for="(caseItem, index) in cornerCases" :key="index">
              <div class="case-header">
                <span class="case-name">{{ caseItem.name }}</span>
                <span class="case-difficulty">{{ caseItem.difficulty }}</span>
              </div>
              <div class="case-visual">
                <div class="cube-preview">
                  <div class="yellow-faces">
                    <div v-for="pos in caseItem.yellowPositions" :key="pos" class="yellow-face" :class="pos"></div>
                  </div>
                </div>
                <div class="case-stats">
                  <span>步数: {{ caseItem.moves.length }}</span>
                  <span>难度: {{ caseItem.difficulty }}</span>
                </div>
              </div>
              <div class="case-formula">
                <div class="formula-display">
                  <span v-for="(move, mIndex) in caseItem.moves" :key="mIndex" class="move-item">{{ move }}</span>
                </div>
                <div class="formula-name">{{ caseItem.formulaName }}</div>
              </div>
              <div class="case-tips">
                <p>{{ caseItem.tips }}</p>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="常见问题" name="faq">
          <div class="faq-content">
            <div class="faq-item" v-for="(item, index) in faqs" :key="index">
              <h4>{{ item.question }}</h4>
              <p>{{ item.answer }}</p>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <div class="bottom-nav">
      <el-button @click="goBack" icon="el-icon-arrow-left" plain>返回CFOP教程</el-button>
      <el-button type="primary" @click="goToPLL" icon="el-icon-arrow-right">学习PLL基础 →</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeTab = ref('overview')

const edgeCases = [
  {
    name: '点 (Dot)',
    formulaName: '十字公式',
    moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\''],
    difficulty: '简单',
    yellowPositions: [],
    tips: '这是最简单的情况，执行十字公式即可。注意观察，这个公式会同时翻转4个棱块。'
  },
  {
    name: '小拐弯 (S-Line)',
    formulaName: '小拐弯公式',
    moves: ['f', 'R', 'U', 'R\'', 'U\'', 'f\''],
    difficulty: '简单',
    yellowPositions: ['top', 'right'],
    tips: '小拐弯可以用标准十字公式，但用f开头的公式更高效。记住小拐弯的位置在右上角。'
  },
  {
    name: '一字 (I-Line)',
    formulaName: '一字公式',
    moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'f', 'R', 'U', 'R\'', 'U\'', 'f\''],
    difficulty: '中等',
    yellowPositions: ['top', 'bottom'],
    tips: '一字是最常见的情况。可以用两次十字公式，或者用组合公式一次完成。'
  }
]

const cornerCases = [
  {
    name: 'Sune',
    formulaName: 'Sune',
    moves: ['R', 'U', 'R\'', 'U', 'R', 'U2', 'R\''],
    difficulty: '简单',
    yellowPositions: ['top', 'front', 'right'],
    tips: 'Sune是最常用的OLL公式之一。黄色面呈现"7"字形。注意最后一步是U2。'
  },
  {
    name: 'Anti-Sune',
    formulaName: 'Anti-Sune',
    moves: ['R\'', 'U\'', 'R', 'U\'', 'R\'', 'U2', 'R'],
    difficulty: '简单',
    yellowPositions: ['top', 'front', 'left'],
    tips: 'Anti-Sune是Sune的镜像。黄色面呈现倒"7"字形。注意用左手执行更流畅。'
  },
  {
    name: 'T-Case',
    formulaName: 'T-Case',
    moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'f', 'R', 'U', 'R\'', 'U\'', 'f\''],
    difficulty: '中等',
    yellowPositions: ['top', 'front', 'right', 'left'],
    tips: 'T-Case有4个黄色角块。可以看作是小拐弯加上Sune的组合。'
  },
  {
    name: 'L-Case',
    formulaName: 'L-Case',
    moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R', 'U\'', 'R\'', 'U', 'R'],
    difficulty: '中等',
    yellowPositions: ['top', 'front', 'back'],
    tips: 'L-Case需要较长的公式。可以拆分为两个部分来记忆：十字公式 + 角块调整。'
  },
  {
    name: 'Pi-Case',
    formulaName: 'Pi-Case',
    moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'R\'', 'U\'', 'R', 'U\'', 'R\'', 'U2', 'R'],
    difficulty: '中等',
    yellowPositions: ['front', 'back', 'left', 'right'],
    tips: 'Pi-Case的黄色面呈现"π"字形。这个公式可以快速翻转所有角块。'
  },
  {
    name: 'U-Case',
    formulaName: 'U-Case',
    moves: ['R\'', 'U\'', 'R', 'U\'', 'R\'', 'U', 'R', 'U', 'R\'', 'U\'', 'R'],
    difficulty: '中等',
    yellowPositions: ['top', 'left', 'right'],
    tips: 'U-Case有3个黄色角块。注意公式的节奏感，U\'和U交替出现。'
  },
  {
    name: 'H-Case',
    formulaName: 'H-Case',
    moves: ['F', 'R', 'U\'', 'R\'', 'U', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R', 'U\'', 'R\'', 'U', 'R'],
    difficulty: '较难',
    yellowPositions: ['front', 'back'],
    tips: 'H-Case只有2个黄色角块在对面。这是两步OLL中最难的情况，但出现概率较低。'
  }
]

const faqs = [
  {
    question: '两步OLL和完整OLL有什么区别？',
    answer: '两步OLL将顶层定向分为两个步骤：先定向棱块（3种情况），再定向角块（7种情况），总共10个算法。完整OLL则是一步完成整个顶层定向，有57种情况。两步OLL适合初学者，学习成本低，可以快速达到sub-30秒水平。'
  },
  {
    question: '如何快速识别OLL情况？',
    answer: '识别OLL情况的关键是看黄色面的形状。先看棱块形成的图案（点、小拐弯、一字），再看角块的黄色分布。建议先记住每种情况的典型特征，然后大量练习，目标是0.5秒内识别出情况。'
  },
  {
    question: '练习OLL的最佳方法是什么？',
    answer: '最佳练习方法是：1）使用计时器，每次还原时记录OLL所用时间；2）使用打乱程序，专门练习OLL；3）练习预判，在F2L最后一步就开始观察OLL情况；4）定期复习，避免遗忘。'
  },
  {
    question: '两步OLL能达到什么水平？',
    answer: '熟练掌握两步OLL后，可以轻松达到sub-30秒的水平。很多速拧选手在达到sub-30秒后才开始学习完整OLL。两步OLL的优势是学习成本低、容错率高，非常适合初学者建立信心。'
  }
]

const progress = computed(() => {
  const tabProgress = {
    overview: 20,
    edge: 50,
    corner: 80,
    faq: 100
  }
  return tabProgress[activeTab.value] || 0
})

const goBack = () => {
  router.push('/tutorial/cfop')
}

const goToPLL = () => {
  router.push('/tutorial/pll-essentials')
}
</script>

<style scoped>
.oll-essentials {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 40px;
  margin-bottom: 20px;
  color: #fff;
}

.header-content h1 {
  font-size: 36px;
  margin-bottom: 10px;
}

.header-content p {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 20px;
}

.header-tags {
  display: flex;
  gap: 10px;
}

.tag {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: bold;
}

.tag.beginner {
  background: rgba(255, 255, 255, 0.2);
}

.tag.algorithm-count {
  background: #4caf50;
}

.progress-bar {
  margin-top: 20px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  margin-bottom: 8px;
}

.nav-tabs {
  margin-bottom: 20px;
}

.overview-content {
  padding: 20px;
}

.overview-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 20px;
}

.overview-card h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 15px;
}

.overview-card p {
  font-size: 15px;
  line-height: 1.8;
  color: #666;
}

.step-flow {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.flow-step {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.flow-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
}

.flow-content h4 {
  font-size: 16px;
  color: #333;
  margin-bottom: 5px;
}

.flow-content p {
  font-size: 14px;
  color: #666;
}

.flow-arrow {
  font-size: 24px;
  color: #999;
}

.tips-card {
  background: #fff3e0;
  border-left: 4px solid #ff9800;
  border-radius: 8px;
  padding: 20px;
}

.tips-card h4 {
  font-size: 16px;
  color: #e65100;
  margin-bottom: 10px;
}

.tips-card ul {
  padding-left: 20px;
}

.tips-card li {
  font-size: 14px;
  line-height: 1.8;
  color: #5d4037;
  margin-bottom: 8px;
}

.cases-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  padding: 20px;
}

.case-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  transition: transform 0.3s ease;
}

.case-card:hover {
  transform: translateY(-3px);
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.case-name {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.case-difficulty {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.case-difficulty.简单 {
  background: #e8f5e9;
  color: #2e7d32;
}

.case-difficulty.中等 {
  background: #fff3e0;
  color: #e65100;
}

.case-difficulty.较难 {
  background: #ffebee;
  color: #c62828;
}

.case-visual {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 15px;
}

.cube-preview {
  width: 80px;
  height: 80px;
  background: #f5f5f5;
  border-radius: 8px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.yellow-faces {
  position: relative;
  width: 60px;
  height: 60px;
}

.yellow-face {
  position: absolute;
  width: 18px;
  height: 18px;
  background: #ffeb3b;
  border-radius: 3px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.yellow-face.top { top: 0; left: 50%; transform: translateX(-50%); }
.yellow-face.bottom { bottom: 0; left: 50%; transform: translateX(-50%); }
.yellow-face.left { left: 0; top: 50%; transform: translateY(-50%); }
.yellow-face.right { right: 0; top: 50%; transform: translateY(-50%); }
.yellow-face.front { top: 50%; left: 50%; transform: translate(-50%, -50%); }
.yellow-face.back { top: 50%; left: 50%; transform: translate(-50%, -50%); opacity: 0.5; }

.case-stats {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 13px;
  color: #666;
}

.case-formula {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 10px;
}

.formula-display {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.move-item {
  background: #667eea;
  color: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: bold;
}

.formula-name {
  font-size: 12px;
  color: #666;
  text-align: center;
}

.case-tips {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.faq-content {
  padding: 20px;
}

.faq-item {
  margin-bottom: 25px;
}

.faq-item:last-child {
  margin-bottom: 0;
}

.faq-item h4 {
  font-size: 16px;
  color: #333;
  margin-bottom: 10px;
}

.faq-item p {
  font-size: 14px;
  line-height: 1.8;
  color: #666;
}

.bottom-nav {
  display: flex;
  justify-content: space-between;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

@media (max-width: 600px) {
  .step-flow {
    flex-direction: column;
  }
  
  .flow-arrow {
    transform: rotate(90deg);
  }
  
  .cases-container {
    grid-template-columns: 1fr;
  }
  
  .bottom-nav {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
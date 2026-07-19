<template>
  <div class="pll-essentials">
    <div class="page-header">
      <div class="header-content">
        <h1>PLL基础</h1>
        <p>两步完成顶层排列 - 仅需6个算法</p>
        <div class="header-tags">
          <span class="tag beginner">初学者路径</span>
          <span class="tag algorithm-count">6个算法</span>
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
        <el-tab-pane label="两步PLL概览" name="overview">
          <div class="overview-content">
            <div class="overview-card">
              <h3>什么是两步PLL？</h3>
              <p>两步PLL是CFOP初学者的最佳起点。它将完整PLL（21种情况）简化为两个步骤，只需学习6个算法就能解决所有顶层排列问题。</p>
            </div>
            <div class="step-flow">
              <div class="flow-step">
                <div class="flow-icon">1</div>
                <div class="flow-content">
                  <h4>第一步：角块排列</h4>
                  <p>将顶层4个角块排列到正确位置，共有2种情况（A-perm）</p>
                </div>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <div class="flow-icon">2</div>
                <div class="flow-content">
                  <h4>第二步：棱块排列</h4>
                  <p>将顶层4个棱块排列到正确位置，共有4种情况</p>
                </div>
              </div>
            </div>
            <div class="tips-card">
              <h4>💡 学习建议</h4>
              <ul>
                <li>先熟练掌握两步PLL，达到sub-30秒后再学习完整PLL</li>
                <li>PLL是最后一步，练习时要注意指法流畅度</li>
                <li>练习预判：在OLL完成前就开始观察PLL情况</li>
                <li>注意中心块颜色，确定正确的位置</li>
              </ul>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="第一步：角块排列" name="corner">
          <div class="cases-container">
            <div class="case-card" v-for="(caseItem, index) in cornerCases" :key="index">
              <div class="case-header">
                <span class="case-name">{{ caseItem.name }}</span>
                <span class="case-difficulty">{{ caseItem.difficulty }}</span>
              </div>
              <div class="case-visual">
                <div class="cube-preview">
                  <div class="corner-preview" :style="{ background: caseItem.pattern }"></div>
                </div>
                <div class="case-stats">
                  <span>步数: {{ caseItem.moves.length }}</span>
                  <span>方向: {{ caseItem.direction }}</span>
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

        <el-tab-pane label="第二步：棱块排列" name="edge">
          <div class="cases-container">
            <div class="case-card" v-for="(caseItem, index) in edgeCases" :key="index">
              <div class="case-header">
                <span class="case-name">{{ caseItem.name }}</span>
                <span class="case-difficulty">{{ caseItem.difficulty }}</span>
              </div>
              <div class="case-visual">
                <div class="cube-preview">
                  <div class="edge-preview" :class="caseItem.patternClass"></div>
                </div>
                <div class="case-stats">
                  <span>步数: {{ caseItem.moves.length }}</span>
                  <span>类型: {{ caseItem.type }}</span>
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
      <el-button @click="goToOLL" icon="el-icon-arrow-left">← 学习OLL基础</el-button>
      <el-button type="primary" @click="goBack" icon="el-icon-arrow-right">返回CFOP教程 →</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeTab = ref('overview')

const cornerCases = [
  {
    name: 'A-perm (顺时针)',
    formulaName: 'A-Permutation Clockwise',
    moves: ['R', 'U', 'R\'', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R\'', 'F', 'R2', 'U\'', 'R\'', 'U\''],
    difficulty: '中等',
    direction: '顺时针',
    pattern: 'linear-gradient(135deg, #ffeb3b 0%, #ffeb3b 50%, transparent 50%, transparent 100%)',
    tips: 'A-perm顺时针会将角块按顺时针方向轮换。公式较长，但节奏感强。注意最后两步是连续的U\'。'
  },
  {
    name: 'A-perm (逆时针)',
    formulaName: 'A-Permutation Counterclockwise',
    moves: ['R\'', 'U\'', 'R', 'F', 'R\'', 'U\'', 'R', 'U', 'R', 'F\'', 'R2', 'U', 'R', 'U'],
    difficulty: '中等',
    direction: '逆时针',
    pattern: 'linear-gradient(225deg, #ffeb3b 0%, #ffeb3b 50%, transparent 50%, transparent 100%)',
    tips: 'A-perm逆时针会将角块按逆时针方向轮换。这是顺时针版本的镜像，可以用左手执行。'
  }
]

const edgeCases = [
  {
    name: 'U-perm (顺时针)',
    formulaName: 'U-Permutation Clockwise',
    moves: ['M2', 'U', 'M2', 'U2', 'M2', 'U', 'M2'],
    difficulty: '简单',
    type: '三棱轮换',
    patternClass: 'pattern-u',
    tips: 'U-perm顺时针会将顶层三个棱块按顺时针方向轮换。这个公式非常对称，容易记忆。M2是中间层180度旋转。'
  },
  {
    name: 'U-perm (逆时针)',
    formulaName: 'U-Permutation Counterclockwise',
    moves: ['M2', 'U\'', 'M2', 'U2', 'M2', 'U\'', 'M2'],
    difficulty: '简单',
    type: '三棱轮换',
    patternClass: 'pattern-u-anti',
    tips: 'U-perm逆时针是顺时针版本的变体，将U改为U\'即可。注意观察棱块的位置变化。'
  },
  {
    name: 'H-perm',
    formulaName: 'H-Permutation',
    moves: ['M2', 'U2', 'M2', 'U2', 'M2'],
    difficulty: '简单',
    type: '双对换',
    patternClass: 'pattern-h',
    tips: 'H-perm会交换对面的两个棱块对。公式非常对称，由M2和U2交替组成。出现概率较高。'
  },
  {
    name: 'Z-perm',
    formulaName: 'Z-Permutation',
    moves: ['M', 'U', 'M2', 'U', 'M2', 'U', 'M'],
    difficulty: '中等',
    type: '双对换',
    patternClass: 'pattern-z',
    tips: 'Z-perm会交换相邻的两个棱块对。这个公式需要注意M层的旋转方向。'
  }
]

const faqs = [
  {
    question: '两步PLL和完整PLL有什么区别？',
    answer: '两步PLL将顶层排列分为两个步骤：先排列角块（2种情况，A-perm），再排列棱块（4种情况，U/H/Z-perm），总共6个算法。完整PLL则是一步完成整个顶层排列，有21种情况。两步PLL适合初学者，学习成本低，可以快速达到sub-30秒水平。'
  },
  {
    question: '如何快速识别PLL情况？',
    answer: '识别PLL情况的关键是看顶层角块和棱块的位置。先看角块是否都在正确位置，如果不在，使用A-perm调整。然后看棱块的位置，确定是U-perm、H-perm还是Z-perm。建议先记住每种情况的典型特征，然后大量练习。'
  },
  {
    question: '练习PLL的最佳方法是什么？',
    answer: '最佳练习方法是：1）使用计时器，每次还原时记录PLL所用时间；2）使用打乱程序，专门练习PLL；3）练习预判，在OLL完成前就开始观察PLL情况；4）注意指法，特别是M层的旋转；5）定期复习，避免遗忘。'
  },
  {
    question: '两步PLL能达到什么水平？',
    answer: '熟练掌握两步PLL后，可以轻松达到sub-30秒的水平。很多速拧选手在达到sub-30秒后才开始学习完整PLL。两步PLL的优势是学习成本低、容错率高，非常适合初学者建立信心。'
  },
  {
    question: '什么是M层旋转？',
    answer: 'M层是魔方的中间层，位于R层和L层之间。M表示顺时针旋转中间层（从右侧看），M\'表示逆时针旋转，M2表示180度旋转。M层旋转是PLL中非常重要的技巧，可以快速调整棱块位置。'
  }
]

const progress = computed(() => {
  const tabProgress = {
    overview: 20,
    corner: 50,
    edge: 80,
    faq: 100
  }
  return tabProgress[activeTab.value] || 0
})

const goBack = () => {
  router.push('/tutorial/cfop')
}

const goToOLL = () => {
  router.push('/tutorial/oll-essentials')
}
</script>

<style scoped>
.pll-essentials {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
  background: linear-gradient(135deg, #f093fb, #f5576c);
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
  display: flex;
  align-items: center;
  justify-content: center;
}

.corner-preview {
  width: 60px;
  height: 60px;
  border-radius: 8px;
}

.edge-preview {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background: #f5f5f5;
  position: relative;
}

.pattern-u::after {
  content: '';
  position: absolute;
  top: 5px;
  left: 5px;
  right: 5px;
  height: 8px;
  background: #ffeb3b;
  border-radius: 4px;
}

.pattern-u-anti::after {
  content: '';
  position: absolute;
  bottom: 5px;
  left: 5px;
  right: 5px;
  height: 8px;
  background: #ffeb3b;
  border-radius: 4px;
}

.pattern-h::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 5px;
  right: 5px;
  height: 8px;
  background: #ffeb3b;
  border-radius: 4px;
  transform: translateY(-50%);
}

.pattern-z::after {
  content: '';
  position: absolute;
  top: 20%;
  left: 20%;
  width: 8px;
  height: 60%;
  background: #ffeb3b;
  border-radius: 4px;
  transform: rotate(45deg);
}

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
  background: #f093fb;
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
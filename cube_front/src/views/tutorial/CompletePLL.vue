<template>
  <div class="complete-pll">
    <div class="page-header">
      <div class="header-content">
        <h1>完整PLL</h1>
        <p>一步完成顶层排列 - 掌握21种情况</p>
        <div class="header-tags">
          <span class="tag advanced">进阶路径</span>
          <span class="tag algorithm-count">21个算法</span>
        </div>
      </div>
    </div>

    <div class="nav-tabs">
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="学习指南" name="guide">
          <div class="guide-content">
            <div class="guide-card">
              <h3>完整PLL学习路线</h3>
              <p>完整PLL共有21种情况。建议按以下顺序分组学习：</p>
              <div class="learning-stages">
                <div class="stage" v-for="(stage, index) in learningStages" :key="index">
                  <div class="stage-number">{{ index + 1 }}</div>
                  <div class="stage-content">
                    <h4>{{ stage.title }}</h4>
                    <p>{{ stage.description }}</p>
                    <div class="stage-cases">
                      <span v-for="caseName in stage.cases" :key="caseName" class="case-tag">{{ caseName }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="tips-card">
              <h4>💡 学习建议</h4>
              <ul>
                <li>先掌握两步PLL的6个算法，再逐步扩展</li>
                <li>PLL是最后一步，重点练习指法流畅度</li>
                <li>学习多个公式变体，选择最短或最顺手的</li>
                <li>练习预判，在OLL完成前就开始观察PLL情况</li>
              </ul>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="角块排列 (Corner)" name="corner">
          <div class="cases-container">
            <div class="case-card" v-for="(caseItem, index) in cornerCases" :key="index">
              <div class="case-header">
                <span class="case-name">{{ caseItem.name }}</span>
                <span class="case-probability">{{ caseItem.probability }}</span>
              </div>
              <div class="case-formula">
                <div class="formula-display">
                  <span v-for="(move, mIndex) in caseItem.moves" :key="mIndex" class="move-item">{{ move }}</span>
                </div>
              </div>
              <div class="case-tips">
                <p>{{ caseItem.tips }}</p>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="棱块排列 (Edge)" name="edge">
          <div class="cases-container">
            <div class="case-card" v-for="(caseItem, index) in edgeCases" :key="index">
              <div class="case-header">
                <span class="case-name">{{ caseItem.name }}</span>
                <span class="case-probability">{{ caseItem.probability }}</span>
              </div>
              <div class="case-formula">
                <div class="formula-display">
                  <span v-for="(move, mIndex) in caseItem.moves" :key="mIndex" class="move-item">{{ move }}</span>
                </div>
              </div>
              <div class="case-tips">
                <p>{{ caseItem.tips }}</p>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="角棱排列 (Corner+Edge)" name="both">
          <div class="cases-container">
            <div class="case-card" v-for="(caseItem, index) in bothCases" :key="index">
              <div class="case-header">
                <span class="case-name">{{ caseItem.name }}</span>
                <span class="case-probability">{{ caseItem.probability }}</span>
              </div>
              <div class="case-formula">
                <div class="formula-display">
                  <span v-for="(move, mIndex) in caseItem.moves" :key="mIndex" class="move-item">{{ move }}</span>
                </div>
              </div>
              <div class="case-tips">
                <p>{{ caseItem.tips }}</p>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <div class="bottom-nav">
      <el-button @click="goToCompleteOLL" icon="el-icon-arrow-left">← 学习完整OLL</el-button>
      <el-button type="primary" @click="goBack" icon="el-icon-arrow-right">返回CFOP教程 →</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeTab = ref('guide')

const learningStages = [
  {
    title: '两步PLL基础',
    description: '先掌握两步PLL的6个算法（A-perm x2 + U/H/Z-perm x4）',
    cases: ['A-perm', 'U-perm', 'H-perm', 'Z-perm']
  },
  {
    title: '角块排列',
    description: '学习所有角块排列PLL情况',
    cases: ['A', 'E', 'F', 'G', 'J', 'N', 'R', 'T', 'U', 'V', 'Y']
  },
  {
    title: '棱块排列',
    description: '学习所有棱块排列PLL情况',
    cases: ['U', 'H', 'Z', 'E', 'F']
  },
  {
    title: '角棱排列',
    description: '学习同时涉及角块和棱块的PLL情况',
    cases: ['P', 'Q', 'S', 'X', 'Y']
  }
]

const cornerCases = [
  {
    name: 'A-perm (顺时针)',
    moves: ['R', 'U', 'R\'', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R\'', 'F', 'R2', 'U\'', 'R\'', 'U\''],
    probability: '12.7%',
    tips: '最常见的角块排列。将3个角块顺时针轮换。'
  },
  {
    name: 'A-perm (逆时针)',
    moves: ['R\'', 'U\'', 'R', 'F', 'R\'', 'U\'', 'R', 'U', 'R', 'F\'', 'R2', 'U', 'R', 'U'],
    probability: '12.7%',
    tips: 'A-perm的镜像。将3个角块逆时针轮换。'
  },
  {
    name: 'E-perm',
    moves: ['R2', 'U\'', 'R', 'U\'', 'R', 'U', 'R\'', 'U', 'R', 'U\'', 'R\'', 'U', 'R', 'U\'', 'R2'],
    probability: '4.8%',
    tips: 'E-perm交换两对对角的角块。'
  },
  {
    name: 'F-perm',
    moves: ['R', 'U\'', 'R\'', 'U\'', 'R', 'U', 'R\'', 'F\'', 'R', 'U\'', 'R\'', 'U\'', 'R\'', 'F', 'R'],
    probability: '4.8%',
    tips: 'F-perm同时调整角块和棱块。'
  }
]

const edgeCases = [
  {
    name: 'U-perm (顺时针)',
    moves: ['M2', 'U', 'M2', 'U2', 'M2', 'U', 'M2'],
    probability: '12.7%',
    tips: '最常见的棱块排列。将3个棱块顺时针轮换。'
  },
  {
    name: 'U-perm (逆时针)',
    moves: ['M2', 'U\'', 'M2', 'U2', 'M2', 'U\'', 'M2'],
    probability: '12.7%',
    tips: 'U-perm的变体，将U改为U\'。'
  },
  {
    name: 'H-perm',
    moves: ['M2', 'U2', 'M2', 'U2', 'M2'],
    probability: '9.5%',
    tips: 'H-perm交换对面的两个棱块对。公式非常对称。'
  },
  {
    name: 'Z-perm',
    moves: ['M', 'U', 'M2', 'U', 'M2', 'U', 'M'],
    probability: '9.5%',
    tips: 'Z-perm交换相邻的两个棱块对。'
  },
  {
    name: 'E-perm',
    moves: ['M2', 'U\'', 'M\'', 'U2', 'M', 'U\'', 'M2'],
    probability: '4.8%',
    tips: 'E-perm交换两对对角的棱块。'
  }
]

const bothCases = [
  {
    name: 'P-perm',
    moves: ['R', 'U', 'R\'', 'U\'', 'R\'', 'F', 'R', 'F\'', 'U', 'R\'', 'U\'', 'R', 'U', 'R\'', 'U\'', 'R'],
    probability: '4.8%',
    tips: 'P-perm同时调整角块和棱块。'
  },
  {
    name: 'Q-perm',
    moves: ['R\'', 'U\'', 'R', 'U', 'R', 'F', 'R\'', 'F\'', 'U\'', 'R', 'U', 'R\'', 'U\'', 'R', 'U', 'R\''],
    probability: '4.8%',
    tips: 'Q-perm是P-perm的变体。'
  },
  {
    name: 'S-perm',
    moves: ['R', 'U\'', 'R\'', 'U', 'R\'', 'F', 'R', 'U', 'R\'', 'U\'', 'R\'', 'F\'', 'R', 'U', 'R\''],
    probability: '4.8%',
    tips: 'S-perm同时调整角块和棱块。'
  },
  {
    name: 'X-perm',
    moves: ['R2', 'D2', 'R\'', 'U\'', 'R', 'D2', 'R\'', 'U', 'R\''],
    probability: '4.8%',
    tips: 'X-perm需要转体，或者学习不转体的公式。'
  },
  {
    name: 'Y-perm',
    moves: ['F', 'R', 'U\'', 'R\'', 'U\'', 'R', 'U', 'R\'', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R\'', 'F', 'R', 'F\''],
    probability: '4.8%',
    tips: 'Y-perm是最难的PLL之一，但出现概率较低。'
  }
]

const goBack = () => {
  router.push('/tutorial/cfop')
}

const goToCompleteOLL = () => {
  router.push('/tutorial/complete-oll')
}
</script>

<style scoped>
.complete-pll {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
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

.tag.advanced {
  background: rgba(255, 255, 255, 0.2);
}

.tag.algorithm-count {
  background: #ff9800;
}

.nav-tabs {
  margin-bottom: 20px;
}

.guide-content {
  padding: 20px;
}

.guide-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 20px;
}

.guide-card h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 15px;
}

.guide-card p {
  font-size: 15px;
  line-height: 1.8;
  color: #666;
  margin-bottom: 20px;
}

.learning-stages {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.stage {
  display: flex;
  gap: 15px;
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stage-number {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #43e97b, #38f9d7);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
}

.stage-content h4 {
  font-size: 16px;
  color: #333;
  margin-bottom: 5px;
}

.stage-content p {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.stage-cases {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.case-tag {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.tips-card {
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
  border-radius: 8px;
  padding: 20px;
}

.tips-card h4 {
  font-size: 16px;
  color: #1565c0;
  margin-bottom: 10px;
}

.tips-card ul {
  padding-left: 20px;
}

.tips-card li {
  font-size: 14px;
  line-height: 1.8;
  color: #0d47a1;
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

.case-probability {
  padding: 4px 12px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
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
}

.move-item {
  background: #43e97b;
  color: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: bold;
}

.case-tips {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.bottom-nav {
  display: flex;
  justify-content: space-between;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

@media (max-width: 600px) {
  .cases-container {
    grid-template-columns: 1fr;
  }
  
  .bottom-nav {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
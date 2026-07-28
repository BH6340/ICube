<template>
  <div class="complete-oll">
    <div class="page-header">
      <div class="header-content">
        <h1>完整OLL</h1>
        <p>一步完成顶层定向 - 掌握57种情况</p>
        <div class="header-tags">
          <span class="tag advanced">进阶路径</span>
          <span class="tag algorithm-count">57个算法</span>
        </div>
      </div>
    </div>

    <div class="nav-tabs">
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="学习指南" name="guide">
          <div class="guide-content">
            <div class="guide-card">
              <h3>完整OLL学习路线</h3>
              <p>完整OLL共有57种情况。建议按以下顺序分组学习：</p>
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
                <li>每天学习5-10个新算法，同时复习之前学过的</li>
                <li>使用算法训练工具进行随机练习</li>
                <li>重点练习出现概率高的情况</li>
                <li>学习多个公式变体，选择最适合自己的</li>
              </ul>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane v-for="(group, index) in ollGroups" :key="index" :label="group.name" :name="group.name">
          <div class="cases-container">
            <div class="case-card" v-for="(caseItem, cIndex) in group.cases" :key="cIndex">
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
      <el-button @click="goBack" icon="el-icon-arrow-left" plain>返回CFOP教程</el-button>
      <el-button type="primary" @click="goToCompletePLL" icon="el-icon-arrow-right">学习完整PLL →</el-button>
    </div>
  </div>
</template>

<script setup>
/**
 * CompleteOLL.vue - 完整 OLL 教程页面
 *
 * 核心职责：
 * 1. 展示 OLL（定向最后一层）完整算法集
 * 2. 按学习阶段组织内容：基础 → 进阶 → 完整
 * 3. 提供每个 case 的公式和分类信息
 *
 * 功能特性：
 *   - Tab 切换不同学习阶段
 *   - 每个 case 展示公式列表和适用场景
 *   - 支持跳转到公式详情
 *
 * 设计要点：
 *   - learningStages 数组按算法数量分级组织
 *   - activeTab 追踪当前选中的学习阶段
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeTab = ref('guide')

const learningStages = [
  {
    title: '两步OLL基础',
    description: '先掌握两步OLL的10个算法，这是学习完整OLL的基础',
    cases: ['Sune', 'Anti-Sune', 'T-Case', 'L-Case', 'Pi-Case']
  },
  {
    title: '十字系列',
    description: '包含所有有十字特征的OLL情况',
    cases: ['Cross', 'T', 'L', 'S', 'Pi']
  },
  {
    title: '点系列',
    description: '包含所有点特征的OLL情况',
    cases: ['Dot', 'U', 'H', 'Z']
  },
  {
    title: '其他情况',
    description: '剩余的OLL情况',
    cases: ['E', 'F', 'G', 'N', 'V', 'W', 'Y']
  }
]

const ollGroups = [
  {
    name: '十字系列',
    cases: [
      {
        name: 'T-Case',
        moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'f', 'R', 'U', 'R\'', 'U\'', 'f\''],
        probability: '9.3%',
        tips: '最常见的OLL情况之一。可以用两次小拐弯公式完成。'
      },
      {
        name: 'L-Case',
        moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R', 'U\'', 'R\'', 'U', 'R'],
        probability: '9.3%',
        tips: 'L-Case有多种公式变体，选择最适合自己的。'
      },
      {
        name: 'S-Case',
        moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'R', 'U\'', 'R\'', 'U', 'R', 'U\'', 'R\''],
        probability: '4.6%',
        tips: 'S-Case是T-Case的变体，注意区分。'
      },
      {
        name: 'Pi-Case',
        moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'R\'', 'U\'', 'R', 'U\'', 'R\'', 'U2', 'R'],
        probability: '4.6%',
        tips: 'Pi-Case的黄色面呈现π字形。'
      }
    ]
  },
  {
    name: '点系列',
    cases: [
      {
        name: 'Dot',
        moves: ['F', 'R', 'U', 'R\'', 'U\'', 'F\'', 'f', 'R', 'U', 'R\'', 'U\'', 'f\''],
        probability: '4.6%',
        tips: '点是两步OLL的起点。用十字公式+Sune组合。'
      },
      {
        name: 'U-Case',
        moves: ['R\'', 'U\'', 'R', 'U\'', 'R\'', 'U', 'R', 'U', 'R\'', 'U\'', 'R'],
        probability: '4.6%',
        tips: 'U-Case有3个黄色角块。注意公式的节奏感。'
      },
      {
        name: 'H-Case',
        moves: ['F', 'R', 'U\'', 'R\'', 'U', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R', 'U\'', 'R\'', 'U', 'R'],
        probability: '1.5%',
        tips: 'H-Case只有2个黄色角块在对面。'
      },
      {
        name: 'Z-Case',
        moves: ['R', 'U\'', 'R\'', 'U\'', 'R', 'U', 'R\'', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R\'', 'F', 'R'],
        probability: '1.5%',
        tips: 'Z-Case的黄色面呈现Z字形。'
      }
    ]
  },
  {
    name: 'Sune系列',
    cases: [
      {
        name: 'Sune',
        moves: ['R', 'U', 'R\'', 'U', 'R', 'U2', 'R\''],
        probability: '4.6%',
        tips: '最常用的OLL公式之一。黄色面呈现7字形。'
      },
      {
        name: 'Anti-Sune',
        moves: ['R\'', 'U\'', 'R', 'U\'', 'R\'', 'U2', 'R'],
        probability: '4.6%',
        tips: 'Sune的镜像。用左手执行更流畅。'
      },
      {
        name: 'Sune+',
        moves: ['R', 'U', 'R\'', 'U', 'R', 'U', 'R\'', 'U\'', 'R', 'U2', 'R\''],
        probability: '3.0%',
        tips: 'Sune的扩展情况。'
      },
      {
        name: 'Anti-Sune+',
        moves: ['R\'', 'U\'', 'R', 'U\'', 'R\'', 'U\'', 'R', 'U', 'R\'', 'U2', 'R'],
        probability: '3.0%',
        tips: 'Anti-Sune的扩展情况。'
      }
    ]
  },
  {
    name: '其他情况',
    cases: [
      {
        name: 'E-Case',
        moves: ['R\'', 'U2', 'R', 'U\'', 'R\'', 'U', 'R', 'U\'', 'R\'', 'U', 'R'],
        probability: '1.5%',
        tips: 'E-Case的黄色面呈现E字形。'
      },
      {
        name: 'F-Case',
        moves: ['R', 'U', 'R\'', 'U\'', 'R\'', 'F', 'R', 'F\'', 'U', 'R\'', 'U\'', 'R'],
        probability: '1.5%',
        tips: 'F-Case的黄色面呈现F字形。'
      },
      {
        name: 'G-Case',
        moves: ['R\'', 'U\'', 'R', 'U\'', 'R', 'U', 'R\'', 'U\'', 'R', 'U', 'R\'', 'U', 'R'],
        probability: '3.0%',
        tips: 'G-Case有多种变体，注意区分。'
      },
      {
        name: 'V-Case',
        moves: ['R\'', 'U\'', 'R', 'U', 'R\'', 'U\'', 'R', 'F\'', 'R', 'U', 'R\'', 'U\'', 'R\'', 'F', 'R'],
        probability: '1.5%',
        tips: 'V-Case的黄色面呈现V字形。'
      }
    ]
  }
]

const goBack = () => {
  router.push('/tutorial/cfop')
}

const goToCompletePLL = () => {
  router.push('/tutorial/complete-pll')
}
</script>

<style scoped>
.complete-oll {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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
  background: linear-gradient(135deg, #4facfe, #00f2fe);
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
  background: #4facfe;
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
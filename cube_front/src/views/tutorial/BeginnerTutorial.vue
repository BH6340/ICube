<template>
  <div class="tutorial-container">
    <div class="tutorial-header">
      <h1>三阶魔方入门教程</h1>
      <p class="subtitle">层先法 - 7步还原魔方</p>
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

            <div class="step-target">
              <h3>目标状态</h3>
              <div v-if="steps[currentStep].targetImage" class="target-image">
                <el-image :src="steps[currentStep].targetImage" fit="cover" />
              </div>
              <div v-else class="target-image placeholder">
                <span class="placeholder-icon">🎲</span>
                <span class="placeholder-text">目标状态示意图</span>
              </div>
              <p>{{ steps[currentStep].targetDesc }}</p>
            </div>

            <div class="step-content">
              <div v-html="steps[currentStep].content"></div>
            </div>

            <div v-if="steps[currentStep].formula && steps[currentStep].formula.length > 0" class="step-formula">
              <h3>核心公式</h3>
              <div v-for="(formula, fIndex) in steps[currentStep].formula" :key="fIndex" class="formula-group">
                <div class="formula-box">
                  <span v-for="(move, mIndex) in formula" :key="mIndex" class="formula-item">{{ move }}</span>
                </div>
              </div>
            </div>

            <div v-if="steps[currentStep].tips" class="step-tips">
              <h3>小贴士</h3>
              <ul>
                <li v-for="(tip, i) in steps[currentStep].tips" :key="i">{{ tip }}</li>
              </ul>
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
  </div>
</template>

<script setup>
/**
 * BeginnerTutorial.vue - 新手入门教程页面
 *
 * 核心职责：
 * 1. 展示魔方入门层先法教程
 * 2. 分步指导从底十字到顶面的完整流程
 * 3. 提供目标图示和操作说明
 *
 * 功能特性：
 *   - 步骤式引导，currentStep 追踪当前进度
 *   - 每步骤提供目标图示和 HTML 富文本内容
 *   - 支持上一步/下一步导航
 *
 * 设计要点：
 *   - steps 数组存储各步骤的目标图、描述和内容
 *   - 内容以 HTML 字符串存储，通过 v-html 渲染
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentStep = ref(0)

const steps = [
  {
    title: '第一步：对好第一面十字',
    subtitle: '建立白色底面十字',
    targetImage: 'https://aka.doubaocdn.com/s/tmLs1wo1lu',
    targetDesc: '目标：白色底面十字，四个侧面的棱与中心块同色',
    content: `
      <p>首先我们要对好白色底面的十字。步骤如下：</p>
      <ol>
        <li><strong>做一朵小花：</strong>把四个白色棱块转到黄色中心面，形成一朵白色小花</li>
        <li><strong>转成十字：</strong>把小花的四个白色棱块逐一翻到白色底面</li>
        <li><strong>对齐侧面：</strong>调整顶层，让每个侧面的棱块颜色与中心块一致</li>
      </ol>
      <p><strong>关键点：</strong>对于B和D位置，一步就可以转到顶层；对于A和C位置，转一下侧面就会变到B和D位置。如果有白色棱块挡着，就转一下顶层让个空位。</p>
    `,
    formula: [['F', 'R', 'U', 'R\'', 'U\'', 'F\'']],
    tips: [
      '先做小花再转十字，这样更容易',
      '侧面颜色不需要对齐时就可以翻下去',
      '最后检查每个侧面的棱是否与中心同色'
    ]
  },
  {
    title: '第二步：对好第一面加T字形',
    subtitle: '还原白色底面四个角块',
    targetImage: 'https://aka.doubaocdn.com/s/Gp4Y1wo1lu',
    targetDesc: '目标：白色底面完整，四个侧面形成T字形',
    content: `
      <p>这一步我们要还原白色底面的四个角块。含有白色的角块只有6种可能位置：</p>
      <ul>
        <li><strong>A和B位置（标准情况）：</strong>白色角块在顶层或中层，只需3步公式</li>
        <li><strong>C、D、E、F位置：</strong>需要先转换成A或B位置</li>
      </ul>
      <p><strong>核心公式（A位置）：</strong>F D F'</p>
      <p><strong>注意：</strong>一定要先把白色角块放在正确的目标位置下面，再做公式。否则T字形不会出来。</p>
    `,
    formula: [['F', 'D', 'F\'']],
    tips: [
      '先找A或B位置的角块，这样最省事',
      '角块要放在正确的目标位置下方',
      '做完后检查侧面是否形成T字形'
    ]
  },
  {
    title: '第三步：对好前两层',
    subtitle: '还原中间两层的四个棱块',
    targetImage: '',
    targetDesc: '目标：白色底面和中间两层完全还原',
    content: `
      <p>这一步我们要还原中间两层的四个棱块。顶层的棱块有两种情况：</p>
      <ul>
        <li><strong>情况1（左）：</strong>棱块在顶层，需要移到左边中间层</li>
        <li><strong>情况2（右）：</strong>棱块在顶层，需要移到右边中间层</li>
      </ul>
      <p><strong>左移公式：</strong>U' L' U L U F U' F'</p>
      <p><strong>右移公式：</strong>U R U' R' U' F' U F</p>
      <p><strong>技巧：</strong>如果中间层的棱块位置不对，可以先用公式把它移到顶层，再用上述公式还原。</p>
    `,
    formula: [['U\'', 'L\'', 'U', 'L', 'U', 'F', 'U\'', 'F\''], ['U', 'R', 'U\'', 'R\'', 'U\'', 'F\'', 'U', 'F']],
    tips: [
      '先找顶层的棱块，不要着急处理中间层的',
      '公式做完后检查中间层是否完整',
      '如果找不到可还原的棱块，随便做一次公式就会出现'
    ]
  },
  {
    title: '第四步：在黄色顶面画十字',
    subtitle: '还原黄色顶面的四个棱块',
    targetImage: 'https://aka.doubaocdn.com/s/iB5v1wo1m2',
    targetDesc: '目标：黄色顶面形成十字（侧面颜色不需要对齐）',
    content: `
      <p>这一步我们要在黄色顶面画出十字。顶面的四个棱块只有4种可能情况：</p>
      <ol>
        <li><strong>点（概率1/8）：</strong>只有中心块是黄色</li>
        <li><strong>小拐弯（概率1/2）：</strong>两个相邻棱块是黄色，要放在右前角</li>
        <li><strong>一字（概率1/4）：</strong>两个相对棱块是黄色，要平行于你</li>
        <li><strong>十字（概率1/8）：</strong>已经完成</li>
      </ol>
      <p><strong>核心公式：</strong>F R U R' U' F'</p>
      <p><strong>用法：</strong>这个公式会按顺序在4种情况中切换。点需要做3次，小拐弯做2次，一字做1次。</p>
    `,
    formula: [['F', 'R', 'U', 'R\'', 'U\'', 'F\'']],
    tips: [
      '只看棱块，角块暂时忽略',
      '一定要按照正确的方向摆放魔方',
      '小拐弯有简便公式可以直接做十字'
    ]
  },
  {
    title: '第五步：对好顶层黄色面',
    subtitle: '还原黄色顶面的四个角块朝向',
    targetImage: 'https://aka.doubaocdn.com/s/E2MA1wo1m2',
    targetDesc: '目标：黄色顶面完全还原',
    content: `
      <p>这一步我们要调整顶层角块的朝向，让整个黄色顶面还原。顶面四角只有8种情况：</p>
      <ul>
        <li><strong>小鱼1：</strong>鱼头在左后角，侧面三个黄色一顺</li>
        <li><strong>小鱼2：</strong>鱼头在左后角，侧面三个黄色另一顺</li>
      </ul>
      <p><strong>小鱼1公式：</strong>R' U' R U' R' U'2 R</p>
      <p><strong>小鱼2公式：</strong>F U F' U F U2 F'</p>
      <p><strong>技巧：</strong>其他6种情况都可以通过做一次小鱼公式转换成小鱼1或小鱼2。</p>
    `,
    formula: [['R\'', 'U\'', 'R', 'U\'', 'R\'', 'U\'2', 'R'], ['F', 'U', 'F\'', 'U', 'F', 'U2', 'F\'']],
    tips: [
      '鱼头一定要放在左后角',
      '做完小鱼公式后，黄色面会变化',
      '最多做2次小鱼公式就能还原'
    ]
  },
  {
    title: '第六步：调整顶层角块位置',
    subtitle: '还原顶层四个角块的正确位置',
    targetImage: '',
    targetDesc: '目标：顶层四个角块位置正确（颜色可能不对）',
    content: `
      <p>这一步我们要调整顶层四个角块的位置，让它们归位。方法如下：</p>
      <ol>
        <li><strong>找归位的角块：</strong>转动顶层，看看有没有角块的侧面颜色与下面两层一致</li>
        <li><strong>摆好位置：</strong>把归位的角块放在右前角</li>
        <li><strong>做公式：</strong>R2 D2 R' U' R D2 R' U R'</li>
      </ol>
      <p><strong>技巧：</strong>如果没有归位的角块，随便做一次公式就会出现。</p>
    `,
    formula: [['R2', 'D2', 'R\'', 'U\'', 'R', 'D2', 'R\'', 'U', 'R\'']],
    tips: [
      '先找已经归位的角块',
      '归位的角块放在右前角',
      '做完公式后检查角块位置'
    ]
  },
  {
    title: '第七步：调整顶层棱块位置',
    subtitle: '还原顶层四个棱块的正确位置',
    targetImage: '',
    targetDesc: '目标：魔方完全还原！',
    content: `
      <p>最后一步，我们要调整顶层四个棱块的位置，完成魔方还原。方法如下：</p>
      <ol>
        <li><strong>找归位的棱块：</strong>转动顶层，看看有没有棱块的颜色与下面两层一致</li>
        <li><strong>摆好位置：</strong>把归位的面放在后面</li>
        <li><strong>做公式：</strong>F2 U L R' F2 L' R U F2</li>
      </ol>
      <p><strong>技巧：</strong>如果没有归位的棱块，随便做一次公式就会出现。</p>
      <p><strong>恭喜你！</strong>完成这一步后，你的魔方就完全还原了！</p>
    `,
    formula: [['F2', 'U', 'L', 'R\'', 'F2', 'L\'', 'R', 'U', 'F2']],
    tips: [
      '先找已经归位的棱块',
      '归位的面放在后面',
      '做完公式后检查魔方是否完全还原',
      '如果还没还原，再做一次公式'
    ]
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

.step-target {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.step-target h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 10px;
}

.target-image {
  width: 200px;
  height: 200px;
  margin: 10px 0;
  border-radius: 8px;
  overflow: hidden;
}

.target-image img {
  width: 100%;
  height: 100%;
}

.target-image.placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: #e9ecef;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.placeholder-text {
  font-size: 14px;
  color: #6c757d;
}

.step-target p {
  font-size: 14px;
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

.step-nav {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
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

  .target-image {
    width: 150px;
    height: 150px;
  }
}
</style>
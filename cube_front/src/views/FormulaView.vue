<template>
  <div class="formula-view-container">
    <FormulaLibrary @play-formula="handlePlayFormula" />
  </div>
</template>

<script setup>
/**
 * FormulaView.vue - 公式库页面视图
 *
 * 核心职责：
 * 1. 作为公式库的容器页面，嵌入 FormulaLibrary 组件
 * 2. 接收公式播放事件（预留接口）
 *
 * 设计要点：
 * - 简洁的布局容器，将核心逻辑委托给 FormulaLibrary 组件
 * - 预留 handlePlayFormula 方法，用于未来实现公式快速定位功能
 */
import FormulaLibrary from '../components/formula/FormulaLibrary.vue'

/**
 * 处理公式播放事件
 *
 * 当用户点击公式的播放按钮时触发，预留的回调接口。
 * 未来可用于跳转到 3D 演示页面或滚动到指定公式位置。
 *
 * @param {Object} formula - 公式对象
 */
const handlePlayFormula = (formula) => {
}
</script>

<style scoped>
.formula-view-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}
</style>
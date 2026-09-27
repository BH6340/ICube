<template>
  <el-tooltip placement="top" effect="light" :show-after="200">
    <template #content>
      <div class="step-tooltip-card">
        <div class="step-tooltip-title">{{ title }}（{{ steps.length }}步）</div>
        <div class="step-tooltip-chips">
          <span v-for="(step, i) in steps" :key="i" class="step-chip">{{ step }}</span>
        </div>
      </div>
    </template>
    <slot></slot>
  </el-tooltip>
</template>

<script setup>
/**
 * StepTooltip - 步骤序列悬停弹窗
 *
 * 用法：
 *   <StepTooltip :steps="['R', 'U', 'R\'', ...]" title="复原步骤">
 *     <span>45步</span>
 *   </StepTooltip>
 */
defineProps({
  steps: {
    type: Array,
    default: () => []
  },
  title: {
    type: String,
    default: '步骤序列'
  }
})
</script>

<style scoped>
.step-tooltip-card {
  max-width: 360px;
  padding: 12px 16px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.step-tooltip-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.step-tooltip-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.step-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 6px;
  font-size: 12px;
  font-weight: 500;
  color: #606266;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
}
</style>

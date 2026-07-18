<template>
  <div class="formula-view-container">
    <FormulaLibrary @play-formula="handlePlayFormula" />
  </div>
</template>

<script setup>
import FormulaLibrary from '../components/formula/FormulaLibrary.vue'

const handlePlayFormula = (formula) => {
}
</script>

<style scoped>
.formula-view-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}
</style>
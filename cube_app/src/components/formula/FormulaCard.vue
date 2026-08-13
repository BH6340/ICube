<template>
  <div class="formula-card" @click="$emit('click', formula)">
    <!-- 缩略图 -->
    <div class="card-thumb">
      <img
        v-if="thumbUrl"
        :src="thumbUrl"
        alt="缩略图"
        class="thumb-img"
      />
      <van-icon v-else name="photo-o" size="40" class="thumb-placeholder" />
    </div>

    <!-- 公式信息 -->
    <div class="card-info">
      <div class="card-header">
        <span class="card-name">{{ formula.name }}</span>
        <van-tag :type="difficultyType" size="medium">{{ difficultyText }}</van-tag>
      </div>
      <div class="card-notation">{{ formula.notation }}</div>
      <div class="card-footer">
        <span class="card-meta">{{ categoryName }} · {{ authorName }}</span>
        <van-icon
          :name="collected ? 'like' : 'like-o'"
          :color="collected ? '#ee0a24' : '#969799'"
          size="20"
          class="collect-icon"
          @click.stop="$emit('collect', formula)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * FormulaCard.vue - 移动端公式卡片组件
 *
 * 布局：flex 横向，左侧缩略图（80×80px），右侧公式信息
 */
import { computed } from 'vue'
import { buildMediaUrl } from '@/utils/media-url'

const props = defineProps({
  formula: { type: Object, required: true },
  collected: { type: Boolean, default: false }
})

defineEmits(['click', 'collect'])

// 缩略图 URL：后端 FormulaSerializer 返回 thumbnail 字段（SerializerMethodField，只读）
const thumbUrl = computed(() => {
  const path = props.formula.thumbnail
  return path ? buildMediaUrl(path) : ''
})

// 难度映射：后端 difficulty 为 IntegerField（1=基础 2=进阶 3+=困难）
const diffKey = computed(() => Number(props.formula.difficulty))
const difficultyText = computed(() => {
  const d = diffKey.value
  if (d === 1) return '基础'
  if (d === 2) return '进阶'
  return '困难'
})
const difficultyType = computed(() => {
  const d = diffKey.value
  if (d === 1) return 'primary'
  if (d === 2) return 'warning'
  return 'danger'
})

// 分类名和作者名（兼容嵌套和扁平两种数据格式）
const categoryName = computed(() => props.formula.category?.name || props.formula.category_name || '未分类')
const authorName = computed(() => props.formula.author?.username || props.formula.author_username || '匿名')
</script>

<style scoped>
.formula-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 8px;
}

.card-thumb {
  flex-shrink: 0;
  width: 80px;
  height: 80px;
  border-radius: 6px;
  background: #f7f8fa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.thumb-placeholder {
  color: #dcdee0;
}

.card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-notation {
  font-family: 'Cascadia Code', Consolas, monospace;
  font-size: 13px;
  color: #646566;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-meta {
  font-size: 12px;
  color: #969799;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collect-icon {
  flex-shrink: 0;
  cursor: pointer;
}
</style>

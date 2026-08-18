<template>
  <div
    class="formula-card"
    :class="{ 'multi-select-mode': multiSelect, selected }"
    @click="onClick"
    @touchstart.passive="onTouchStart"
    @touchend.passive="onTouchEnd"
    @touchmove.passive="onTouchMove"
  >
    <!-- 多选指示器 -->
    <div v-if="multiSelect" class="select-indicator">
      <van-icon :name="selected ? 'checked' : 'circle'" :color="selected ? '#1989fa' : '#c8c9cc'" size="20" />
    </div>

    <!-- 缩略图 -->
    <div class="card-thumb">
      <img
        v-if="thumbUrl"
        :src="thumbUrl"
        alt="缩略图"
        class="thumb-img"
      />
      <van-icon v-else name="photo-o" size="40" class="thumb-placeholder" />
      <van-icon v-if="downloaded" name="down" size="14" color="#07c160" class="downloaded-badge" />
    </div>

    <!-- 公式信息 -->
    <div class="card-info">
      <div class="card-header">
        <span class="card-name">{{ formula.name }}</span>
        <van-tag :type="difficultyType" size="medium">{{ difficultyText }}</van-tag>
      </div>
      <div class="card-notation">{{ formula.notation }}</div>
      <div class="card-footer">
        <span class="card-meta">
          <van-icon name="eye-o" size="13" />{{ viewCount }} · {{ categoryName }} · {{ authorName }}
        </span>
        <van-icon
          v-if="!multiSelect"
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
 * 支持长按进入多选模式
 */
import { computed } from 'vue'
import { buildMediaUrl } from '@/utils/media-url'

const props = defineProps({
  formula: { type: Object, required: true },
  collected: { type: Boolean, default: false },
  downloaded: { type: Boolean, default: false },
  multiSelect: { type: Boolean, default: false },
  selected: { type: Boolean, default: false },
})

const emit = defineEmits(['click', 'collect', 'longpress'])

const thumbUrl = computed(() => {
  const path = props.formula.thumbnail
  return path ? buildMediaUrl(path) : ''
})

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

const categoryName = computed(() => props.formula.category?.name || props.formula.category_name || '未分类')
const authorName = computed(() => props.formula.author?.username || props.formula.author_username || '匿名')
const viewCount = computed(() => props.formula.view_count || 0)

function onClick() {
  emit('click', props.formula)
}

let longPressTimer = null
function onTouchStart() {
  longPressTimer = setTimeout(() => {
    emit('longpress', props.formula)
  }, 500)
}
function onTouchEnd() {
  clearTimeout(longPressTimer)
}
function onTouchMove() {
  clearTimeout(longPressTimer)
}
</script>

<style scoped>
.formula-card {
  display: flex;
  gap: var(--icube-space-md);
  padding: var(--icube-space-md);
  background: var(--icube-bg-2);
  border-radius: var(--icube-radius-md);
  margin-bottom: var(--icube-space-sm);
  transition: background-color 0.2s;
}

.formula-card.multi-select-mode {
  padding-left: var(--icube-space-sm);
}

.formula-card.selected {
  background: #f0f9ff;
  box-shadow: inset 3px 0 0 var(--icube-primary);
}

.select-indicator {
  display: flex;
  align-items: center;
  padding-right: var(--icube-space-xs);
}

.card-thumb {
  flex-shrink: 0;
  width: 80px;
  height: 80px;
  border-radius: var(--icube-radius-sm);
  background: var(--icube-bg-1);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.thumb-placeholder {
  color: var(--van-text-color-3);
}

.downloaded-badge {
  position: absolute;
  bottom: 2px;
  right: 2px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  padding: 1px;
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
  gap: var(--icube-space-sm);
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--icube-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-notation {
  font-family: var(--icube-font-mono);
  font-size: 13px;
  color: var(--icube-text-2);
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
  font-size: var(--icube-font-meta);
  color: var(--icube-text-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collect-icon {
  flex-shrink: 0;
  cursor: pointer;
}
</style>

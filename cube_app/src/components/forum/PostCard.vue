<script setup>
/**
 * PostCard.vue — 帖子卡片组件
 *
 * flex 左右结构：左侧内容自适应，右侧图片固定 140px，垂直居中。
 * 图片 1:1 比例，object-fit: contain，不裁剪。
 */
defineOptions({ name: 'PostCard' })

const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['click'])

import { computed } from 'vue'
import { buildMediaUrl } from '@/utils/media-url'

// 第一张图片作为封面
const coverImage = computed(() => {
  const images = props.post.images || []
  if (images.length === 0) return ''
  const img = images[0]
  return typeof img === 'string' ? buildMediaUrl(img) : buildMediaUrl(img.image || img.url || '')
})

const authorName = computed(() => props.post.author?.username || '匿名')
const authorAvatar = computed(() => buildMediaUrl(props.post.author?.image))

const tagNames = computed(() => {
  const tags = props.post.tags || []
  return tags.map(t => (typeof t === 'object' ? t.name : t))
})

const isPinned = computed(() => props.post.is_pinned)
const isEssence = computed(() => props.post.is_essence)

const relativeTime = computed(() => {
  const date = new Date(props.post.created_at)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
})
</script>

<template>
  <div class="post-card" @click="emit('click', post.id)">
    <!-- 左侧内容区 -->
    <div class="post-main">
      <div class="post-title">
        <span class="title-text">{{ post.title }}</span>
      </div>
      <div class="post-meta">
        <span class="meta-author">{{ authorName }}</span>
        <span class="meta-sep">·</span>
        <span class="meta-time">{{ relativeTime }}</span>
      </div>
      <div class="post-tags">
        <van-tag v-if="isPinned" type="danger" size="mini">置顶</van-tag>
        <van-tag v-if="isEssence" type="warning" size="mini">精华</van-tag>
        <span v-for="tag in tagNames" :key="tag" class="stat-tag">{{ tag }}</span>
      </div>
      <div class="post-stats">
        <van-icon name="eye-o" size="13" />
        <span class="stat-num">{{ post.view_count || 0 }}</span>
        <van-icon name="good-job-o" size="13" class="stat-icon" />
        <span class="stat-num">{{ post.like_count || 0 }}</span>
        <van-icon name="chat-o" size="13" class="stat-icon" />
        <span class="stat-num">{{ post.comment_count || 0 }}</span>
      </div>
    </div>
    <!-- 右侧图片区 -->
    <div v-if="coverImage" class="post-image">
      <img :src="coverImage" alt="" loading="lazy" />
    </div>
  </div>
</template>

<style scoped>
.post-card {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: var(--van-background-2);
  border-radius: 8px;
  margin: 0 12px 8px;
  align-items: center;
}

.post-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.post-title {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tag-pin {
  flex-shrink: 0;
}

.title-text {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--van-text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-meta {
  font-size: 0.75rem;
  color: var(--van-text-color-2);
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-sep {
  opacity: 0.5;
}

.post-tags {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.stat-tag {
  background: var(--van-background);
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 0.7rem;
}

.post-stats {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.72rem;
  color: var(--van-text-color-2);
}

.stat-icon {
  margin-left: 8px;
}

.stat-num {
  margin-left: 2px;
}

.post-image {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.post-image img {
  width: 100%;
  height: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 6px;
}
</style>

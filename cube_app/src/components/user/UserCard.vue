<script setup>
/**
 * UserCard.vue — 用户卡片组件
 *
 * 显示头像、用户名、简介，支持查看主页和关注/取消关注操作。
 */
import { buildMediaUrl } from '@/utils/media-url'

const props = defineProps({
  user: { type: Object, required: true },
  currentUsername: { type: String, default: '' },
  actionLoading: { type: Boolean, default: false },
})

const emit = defineEmits(['view', 'toggle-follow'])

const avatarUrl = computed(() => buildMediaUrl(props.user.image))
const isSelf = computed(() => props.user.username === props.currentUsername)
const isFollowing = computed(() => !!props.user.following)

function onView() {
  emit('view', props.user.username)
}

function onToggleFollow() {
  emit('toggle-follow', props.user)
}
</script>

<template>
  <div class="user-card" @click="onView">
    <van-image round width="44" height="44" :src="avatarUrl" fit="cover">
      <template #error>
        <div class="avatar-fallback">{{ user.username?.[0] || '?' }}</div>
      </template>
    </van-image>
    <div class="card-info">
      <div class="card-name">
        {{ user.username }}
        <van-tag v-if="isSelf" type="primary" size="mini" round>我</van-tag>
      </div>
      <div class="card-bio">{{ user.bio || '这个人很懒，什么都没写' }}</div>
    </div>
    <van-button
      v-if="!isSelf"
      :type="isFollowing ? 'default' : 'primary'"
      size="small"
      round
      :loading="actionLoading"
      @click.stop="onToggleFollow"
    >
      {{ isFollowing ? '已关注' : '关注' }}
    </van-button>
  </div>
</template>

<style scoped>
.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--van-background-2);
  border-radius: 10px;
  margin: 0 12px 8px;
}

.user-card:active {
  opacity: 0.85;
}

.avatar-fallback {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--van-primary-color);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 700;
}

.card-info {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--van-text-color);
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.card-bio {
  font-size: 0.8rem;
  color: var(--van-text-color-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

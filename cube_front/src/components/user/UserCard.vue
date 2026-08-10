<template>
  <article
    class="user-card"
    tabindex="0"
    @click="emit('view', user.username)"
    @keydown.enter.self="emit('view', user.username)"
    @keydown.space.self.prevent="emit('view', user.username)"
  >
    <div class="cube-stripe" aria-hidden="true">
      <span class="stripe-blue"></span>
      <span class="stripe-yellow"></span>
      <span class="stripe-red"></span>
    </div>

    <div class="user-main">
      <el-avatar
        :size="56"
        :src="user.image || defaultAvatar"
        :alt="`${user.username} 的头像`"
      />
      <div class="user-copy">
        <div class="name-row">
          <h2>{{ user.username }}</h2>
          <el-tag v-if="isCurrentUser" size="small" type="success">我</el-tag>
        </div>
        <p>{{ user.bio || '暂无简介' }}</p>
      </div>
    </div>

    <div class="user-actions">
      <el-button plain @click.stop="emit('view', user.username)">
        查看主页
      </el-button>
      <el-button
        v-if="!isCurrentUser"
        :type="user.following ? 'default' : 'primary'"
        :loading="actionLoading"
        @click.stop="emit('toggle-follow', user)"
      >
        {{ user.following ? '已关注' : '关注' }}
      </el-button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import defaultAvatar from '@/assets/default_avatar.svg'

const props = defineProps({
  user: { type: Object, required: true },
  currentUsername: { type: String, default: '' },
  actionLoading: { type: Boolean, default: false }
})

const emit = defineEmits(['view', 'toggle-follow'])

const isCurrentUser = computed(
  () => props.currentUsername === props.user.username
)
</script>

<style scoped>
.user-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 178px;
  padding: 26px 24px 20px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.user-card:hover {
  transform: translateY(-2px);
  border-color: #c6e2ff;
  box-shadow: 0 8px 24px rgba(48, 49, 51, 0.08);
}

.user-card:focus-visible {
  outline: 3px solid rgba(64, 158, 255, 0.35);
  outline-offset: 3px;
}

.cube-stripe {
  position: absolute;
  inset: 0 0 auto;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  height: 5px;
}

.stripe-blue {
  background: #409eff;
}

.stripe-yellow {
  background: #e6a23c;
}

.stripe-red {
  background: #f56c6c;
}

.user-main {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.user-copy {
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-row h2 {
  margin: 0;
  overflow: hidden;
  color: #303133;
  font-size: 18px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-copy p {
  display: -webkit-box;
  margin: 8px 0 0;
  overflow: hidden;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.user-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: auto;
}

.user-actions :deep(.el-button:focus-visible) {
  outline: 3px solid rgba(64, 158, 255, 0.35);
  outline-offset: 2px;
}

@media (max-width: 520px) {
  .user-card {
    padding-inline: 18px;
  }

  .user-actions {
    justify-content: stretch;
  }

  .user-actions :deep(.el-button) {
    flex: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .user-card {
    transition: none;
  }

  .user-card:hover {
    transform: none;
  }
}
</style>

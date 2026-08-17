<template>
  <div class="login-page">
    <van-nav-bar title="登录" />
    <div class="login-header">
      <h2>ICube</h2>
      <p>魔方学习平台</p>
    </div>
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.email"
          name="email"
          label="邮箱"
          placeholder="请输入邮箱"
          :rules="[{ required: true, message: '请填写邮箱' }]"
        />
        <van-field
          v-model="form.password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请填写密码' }]"
        />
      </van-cell-group>
      <div class="login-actions">
        <van-button block type="primary" native-type="submit" :loading="loading">
          登录
        </van-button>
        <router-link to="/register" class="register-link">
          没有账号？去注册
        </router-link>
        <div class="guest-divider">
          <span>或</span>
        </div>
        <van-button block plain class="guest-btn" @click="guestLogin">
          游客登录
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { loginApi } from '@/api/user'
import { useUserStore } from '@/stores/user'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

async function onSubmit() {
  loading.value = true
  try {
    // 后端期望 { user: { email, password } } 格式
    const res = await loginApi({ user: { email: form.email, password: form.password } })
    userStore.setInfo(res.user)
    showToast({ type: 'success', message: '登录成功' })
    router.replace(route.query.redirect || '/formula')
  } catch {
    // request.js 已统一处理错误提示
  } finally {
    loading.value = false
  }
}

function guestLogin() {
  localStorage.setItem('guest', '1')
  showToast({ message: '游客模式' })
  router.replace('/formula')
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--van-gray-1);
}

.login-header {
  text-align: center;
  padding: 2rem 0 1.5rem;
}

.login-header h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--van-primary-color);
  margin-bottom: 0.3rem;
}

.login-header p {
  color: var(--van-gray-6);
  font-size: 0.9rem;
}

.login-actions {
  padding: 1rem 1rem;
}

.register-link {
  display: block;
  text-align: center;
  margin-top: 1rem;
  font-size: 0.875rem;
  color: var(--van-primary-color);
}

.guest-divider {
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
}

.guest-divider::before,
.guest-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--van-gray-4);
}

.guest-divider span {
  padding: 0 0.75rem;
  font-size: 0.75rem;
  color: var(--van-gray-5);
}

.guest-btn {
  color: var(--van-gray-7);
}
</style>

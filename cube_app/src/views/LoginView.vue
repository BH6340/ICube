<template>
  <div class="login-page">
    <van-nav-bar title="登录" />
    <div class="login-header">
      <h2>ICube</h2>
      <p>魔方学习平台</p>
    </div>
    <van-tabs v-model:active="activeTab" sticky>
      <!-- 密码登录 -->
      <van-tab title="密码登录">
        <van-form @submit="onPasswordSubmit">
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
            <div class="login-links">
              <router-link to="/forgot-password" class="link-btn">忘记密码</router-link>
              <router-link to="/register" class="link-btn">没有账号？去注册</router-link>
            </div>
            <div class="guest-divider">
              <span>或</span>
            </div>
            <van-button block plain class="guest-btn" @click="guestLogin">
              游客登录
            </van-button>
          </div>
        </van-form>
      </van-tab>

      <!-- 验证码登录 -->
      <van-tab title="验证码登录">
        <van-form @submit="onCodeSubmit">
          <van-cell-group inset>
            <van-field
              v-model="codeForm.email"
              name="email"
              label="邮箱"
              placeholder="请输入邮箱"
              :rules="[
                { required: true, message: '请填写邮箱' },
                { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '邮箱格式不正确' }
              ]"
            />
            <van-field
              v-model="codeForm.code"
              name="code"
              label="验证码"
              placeholder="请输入6位验证码"
              maxlength="6"
              :rules="[{ required: true, message: '请填写验证码' }]"
            >
              <template #button>
                <van-button size="small" type="primary" plain :disabled="codeCountdown > 0" @click.prevent="handleSendCode('login')">
                  {{ codeCountdown > 0 ? `${codeCountdown}s` : '发送验证码' }}
                </van-button>
              </template>
            </van-field>
          </van-cell-group>
          <div class="login-actions">
            <van-button block type="primary" native-type="submit" :loading="loading">
              登录
            </van-button>
            <div class="login-links">
              <router-link to="/forgot-password" class="link-btn">忘记密码</router-link>
              <router-link to="/register" class="link-btn">没有账号？去注册</router-link>
            </div>
          </div>
        </van-form>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onBeforeUnmount } from 'vue'
import { loginApi, loginWithCodeApi, sendCodeApi } from '@/api/user'
import { useUserStore } from '@/stores/user'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'

const activeTab = ref('password')
const form = reactive({ email: '', password: '' })
const codeForm = reactive({ email: '', code: '' })
const loading = ref(false)
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 验证码倒计时
const codeCountdown = ref(0)
let countdownTimer = null

function startCountdown() {
  codeCountdown.value = 60
  countdownTimer = setInterval(() => {
    codeCountdown.value--
    if (codeCountdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

onBeforeUnmount(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})

async function handleSendCode(action) {
  if (!codeForm.email) {
    showToast({ type: 'fail', message: '请先输入邮箱' })
    return
  }
  try {
    const res = await sendCodeApi({ email: codeForm.email, action })
    if (res.code === 100) {
      showToast({ type: 'success', message: res.msg || '验证码已发送' })
      startCountdown()
    } else {
      showToast({ type: 'fail', message: res.msg || '发送失败' })
    }
  } catch {
    // request.js 已统一处理错误提示
  }
}

async function onPasswordSubmit() {
  loading.value = true
  try {
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

async function onCodeSubmit() {
  loading.value = true
  try {
    const res = await loginWithCodeApi({ email: codeForm.email, code: codeForm.code })
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

.login-links {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
}

.link-btn {
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

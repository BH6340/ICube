<template>
  <div class="reset-page">
    <van-nav-bar title="找回密码" left-arrow @click-left="router.back()" />
    <div class="reset-header">
      <h2>重置密码</h2>
      <p>通过邮箱验证码重置密码</p>
    </div>
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.email"
          name="email"
          label="邮箱"
          placeholder="请输入注册邮箱"
          :rules="[
            { required: true, message: '请填写邮箱' },
            { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '邮箱格式不正确' }
          ]"
        />
        <van-field
          v-model="form.code"
          name="code"
          label="验证码"
          placeholder="请输入6位验证码"
          maxlength="6"
          :rules="[{ required: true, message: '请填写验证码' }]"
        >
          <template #button>
            <van-button size="small" type="primary" plain :disabled="codeCountdown > 0" @click.prevent="handleSendCode">
              {{ codeCountdown > 0 ? `${codeCountdown}s` : '发送验证码' }}
            </van-button>
          </template>
        </van-field>
        <van-field
          v-model="form.newPassword"
          type="password"
          name="newPassword"
          label="新密码"
          placeholder="请输入新密码"
          :rules="[
            { required: true, message: '请填写新密码' },
            { pattern: /^.{6,20}$/, message: '密码长度6-20位' }
          ]"
        />
        <van-field
          v-model="form.confirmPassword"
          type="password"
          name="confirmPassword"
          label="确认密码"
          placeholder="请再次输入新密码"
          :rules="[
            { required: true, message: '请确认密码' },
            { validator: validateConfirm, message: '两次密码不一致' }
          ]"
        />
      </van-cell-group>
      <div class="reset-actions">
        <van-button block type="primary" native-type="submit" :loading="loading">
          重置密码
        </van-button>
        <router-link to="/login" class="login-link">
          返回登录
        </router-link>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { reactive, ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { sendCodeApi, resetPasswordApi } from '@/api/user'

const form = reactive({ email: '', code: '', newPassword: '', confirmPassword: '' })
const loading = ref(false)
const router = useRouter()

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

function validateConfirm() {
  return form.newPassword === form.confirmPassword
}

async function handleSendCode() {
  if (!form.email) {
    showToast({ type: 'fail', message: '请先输入邮箱' })
    return
  }
  try {
    const res = await sendCodeApi({ email: form.email, action: 'reset' })
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

async function onSubmit() {
  loading.value = true
  try {
    const res = await resetPasswordApi({
      email: form.email,
      code: form.code,
      new_password: form.newPassword
    })
    if (res.code === 100) {
      showToast({ type: 'success', message: '密码重置成功，请重新登录' })
      router.replace('/login')
    } else {
      showToast({ type: 'fail', message: res.msg || '重置失败' })
    }
  } catch {
    // request.js 已统一处理错误提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.reset-page {
  min-height: 100vh;
  background: var(--van-gray-1);
}

.reset-header {
  text-align: center;
  padding: 2rem 0 1.5rem;
}

.reset-header h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--van-primary-color);
  margin-bottom: 0.3rem;
}

.reset-header p {
  color: var(--van-gray-6);
  font-size: 0.9rem;
}

.reset-actions {
  padding: 1rem 1rem;
}

.login-link {
  display: block;
  text-align: center;
  margin-top: 1rem;
  font-size: 0.875rem;
  color: var(--van-primary-color);
}
</style>

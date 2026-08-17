<template>
  <div class="register-page">
    <van-nav-bar title="注册" left-arrow @click-left="router.back()" />
    <div class="register-header">
      <h2>ICube</h2>
      <p>创建你的魔方学习账号</p>
    </div>
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          :rules="[
            { required: true, message: '请填写用户名' },
            { pattern: /^[a-zA-Z0-9_\u4e00-\u9fa5]{2,20}$/, message: '2-20位字母、数字、中文或下划线' }
          ]"
        />
        <van-field
          v-model="form.email"
          name="email"
          label="邮箱"
          placeholder="请输入邮箱"
          :rules="[
            { required: true, message: '请填写邮箱' },
            { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '邮箱格式不正确' }
          ]"
        />
        <van-field
          v-model="form.password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[
            { required: true, message: '请填写密码' },
            { pattern: /^.{6,20}$/, message: '密码长度6-20位' }
          ]"
        />
        <van-field
          v-model="form.confirmPassword"
          type="password"
          name="confirmPassword"
          label="确认密码"
          placeholder="请再次输入密码"
          :rules="[
            { required: true, message: '请确认密码' },
            { validator: validateConfirm, message: '两次密码不一致' }
          ]"
        />
      </van-cell-group>
      <div class="register-actions">
        <van-button block type="primary" native-type="submit" :loading="loading">
          注册
        </van-button>
        <router-link to="/login" class="login-link">
          已有账号？去登录
        </router-link>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { registerApi, loginApi } from '@/api/user'
import { useUserStore } from '@/stores/user'

const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const loading = ref(false)
const router = useRouter()
const userStore = useUserStore()

function validateConfirm() {
  return form.password === form.confirmPassword
}

async function onSubmit() {
  loading.value = true
  try {
    await registerApi({
      user: {
        username: form.username,
        email: form.email,
        password: form.password,
      }
    })
    // 注册成功后自动登录
    const loginRes = await loginApi({
      user: { email: form.email, password: form.password }
    })
    userStore.setInfo(loginRes.user)
    showToast({ type: 'success', message: '注册成功' })
    router.replace('/formula')
  } catch {
    // request.js 已统一处理错误提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: var(--van-gray-1);
}

.register-header {
  text-align: center;
  padding: 2rem 0 1.5rem;
}

.register-header h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--van-primary-color);
  margin-bottom: 0.3rem;
}

.register-header p {
  color: var(--van-gray-6);
  font-size: 0.9rem;
}

.register-actions {
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

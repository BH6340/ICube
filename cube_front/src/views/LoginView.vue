<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <h2>登录 ICube</h2>
      <el-tabs v-model="activeTab" class="login-tabs">
        <!-- 密码登录 -->
        <el-tab-pane label="密码登录" name="password">
          <el-form :model="loginForm" :rules="passwordRules" ref="passwordRef" label-position="top">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="loginForm.email" placeholder="example@mail.com"/>
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码"/>
            </el-form-item>

            <el-button type="primary" class="full-width" @click="handlePasswordLogin(passwordRef)">登录</el-button>
          </el-form>
        </el-tab-pane>

        <!-- 验证码登录 -->
        <el-tab-pane label="验证码登录" name="code">
          <el-form :model="codeForm" :rules="codeRules" ref="codeRef" label-position="top">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="codeForm.email" placeholder="example@mail.com"/>
            </el-form-item>

            <el-form-item label="验证码" prop="code">
              <div class="code-row">
                <el-input v-model="codeForm.code" placeholder="请输入6位验证码" maxlength="6"/>
                <el-button type="primary" plain :disabled="codeCountdown > 0" @click="handleSendCode('login')">
                  {{ codeCountdown > 0 ? `${codeCountdown}s` : '发送验证码' }}
                </el-button>
              </div>
            </el-form-item>

            <el-button type="primary" class="full-width" @click="handleCodeLogin(codeRef)">登录</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <div class="auth-footer">
        <el-link type="primary" :underline="false" style="font-size: 14px;" @click="$router.push('/forgot-password')">
          忘记密码？
        </el-link>
        <span style="margin: 0 8px;">|</span>
        <span>新用户？</span>
        <el-link type="primary" :underline="false" style="font-size: 14px;" @click="$router.push('/register')">
          创建账号
        </el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import {ref, reactive, onBeforeUnmount} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {loginApi, loginWithCodeApi, sendCodeApi} from '@/api/user'
import {useUserStore} from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('password')
const passwordRef = ref()
const codeRef = ref()

const loginForm = reactive({email: '', password: ''})
const codeForm = reactive({email: '', code: ''})

const passwordRules = {
  email: [{required: true, message: '请输入邮箱', trigger: 'blur'}],
  password: [{required: true, message: '请输入密码', trigger: 'blur'}]
}

const codeRules = {
  email: [
    {required: true, message: '请输入邮箱', trigger: 'blur'},
    {type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change']}
  ],
  code: [{required: true, message: '请输入验证码', trigger: 'blur'}]
}

// 验证码倒计时
const codeCountdown = ref(0)
let countdownTimer = null

const startCountdown = () => {
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

const handleSendCode = async (action) => {
  if (!codeForm.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  try {
    const res = await sendCodeApi({email: codeForm.email, action})
    if (res.code === 100) {
      ElMessage.success(res.msg || '验证码已发送')
      startCountdown()
    } else {
      ElMessage.error(res.msg || '发送失败')
    }
  } catch (err) {
    console.error('发送验证码失败', err)
  }
}

const handlePasswordLogin = async (formEl) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid) {
      try {
        const res = await loginApi({user: {email: loginForm.email, password: loginForm.password}})
        if (res.code === 100) {
          userStore.setInfo(res.user)
          ElMessage.success('登录成功，欢迎 ' + res.user.username)
          await router.push('/')
        } else {
          ElMessage.error(res.msg || '登录失败')
        }
      } catch (err) {
        console.error('登录失败', err)
      }
    }
  })
}

const handleCodeLogin = async (formEl) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid) {
      try {
        const res = await loginWithCodeApi({email: codeForm.email, code: codeForm.code})
        if (res.code === 100) {
          userStore.setInfo(res.user)
          ElMessage.success('登录成功，欢迎 ' + res.user.username)
          await router.push('/')
        } else {
          ElMessage.error(res.msg || '登录失败')
        }
      } catch (err) {
        console.error('登录失败', err)
      }
    }
  })
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
}

.auth-card {
  width: 400px;
  padding: 20px;
}

.login-tabs {
  margin-bottom: 10px;
}

.full-width {
  width: 100%;
  margin-top: 20px;
}

.code-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

.code-row .el-input {
  flex: 1;
}

.auth-footer {
  margin-top: 15px;
  text-align: center;
  font-size: 14px;
}

h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #409EFF;
}
</style>

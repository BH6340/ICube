<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <h2>注册 ICube 账号</h2>
      <el-form :model="registerForm" :rules="rules" ref="registerRef" label-position="top">
        <!-- 邮箱 -->
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="请输入常用邮箱"/>
        </el-form-item>

        <!-- 验证码 -->
        <el-form-item label="验证码" prop="code">
          <div class="code-row">
            <el-input v-model="registerForm.code" placeholder="请输入6位验证码" maxlength="6"/>
            <el-button type="primary" plain :disabled="codeCountdown > 0" @click="handleSendCode">
              {{ codeCountdown > 0 ? `${codeCountdown}s` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <!-- 密码 -->
        <el-form-item label="密码" prop="password">
          <el-input v-model="registerForm.password" type="password" show-password placeholder="设置密码"/>
        </el-form-item>

        <!-- 确认密码 -->
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" show-password placeholder="再次输入密码"/>
        </el-form-item>

        <el-button type="primary" class="full-width" @click="handleRegister(registerRef)">立即注册</el-button>

        <div class="auth-footer">
          <span>已有账号？</span>
          <el-link type="primary" underline="never" style="font-size: 14px;" @click="$router.push('/login')">
            去登录
          </el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import {ref, reactive, onBeforeUnmount} from 'vue'
import {ElMessage} from 'element-plus'
import {registerWithCodeApi, sendCodeApi} from '@/api/user'
import {useRouter} from "vue-router";

const router = useRouter()
const registerRef = ref()
const registerForm = reactive({
  email: '',
  code: '',
  password: '',
  confirmPassword: ''
})

const validatePass2 = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

const rules = {
  email: [
    {required: true, message: '请输入邮箱', trigger: 'blur'},
    {type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change']}
  ],
  code: [{required: true, message: '请输入验证码', trigger: 'blur'}],
  password: [
    {required: true, message: '请输入密码', trigger: 'blur'},
    {min: 6, message: '密码长度不能少于 6 位', trigger: 'blur'}
  ],
  confirmPassword: [
    {required: true, message: '请再次输入密码', trigger: 'blur'},
    {validator: validatePass2, trigger: 'blur'}
  ]
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

const handleSendCode = async () => {
  if (!registerForm.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  try {
    const res = await sendCodeApi({email: registerForm.email, action: 'register'})
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

const handleRegister = async (formEl) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid) {
      try {
        const res = await registerWithCodeApi({
          email: registerForm.email,
          code: registerForm.code,
          password: registerForm.password
        })
        if (res.code === 100) {
          ElMessage.success('注册成功，请登录')
          await router.push('/login')
        } else {
          ElMessage.error(res.msg || '注册失败')
        }
      } catch (err) {
        console.error('注册失败', err)
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

/* 移动端适配 */
@media (max-width: 480px) {
  .auth-container {
    height: auto;
    padding: 40px 16px;
    min-height: calc(80vh - 60px);
  }

  .auth-card {
    width: 100%;
    max-width: 360px;
    padding: 16px;
  }

  h2 {
    font-size: 20px;
    margin-bottom: 20px;
  }

  .code-row {
    gap: 8px;
  }

  .code-row .el-button {
    padding: 8px 10px;
    font-size: 12px;
    white-space: nowrap;
  }

  .full-width {
    margin-top: 16px;
  }

  .auth-footer {
    margin-top: 12px;
    font-size: 13px;
  }
}
</style>

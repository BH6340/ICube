<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <h2>找回密码</h2>
      <el-form :model="resetForm" :rules="rules" ref="resetRef" label-position="top">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="resetForm.email" placeholder="请输入注册邮箱"/>
        </el-form-item>

        <el-form-item label="验证码" prop="code">
          <div class="code-row">
            <el-input v-model="resetForm.code" placeholder="请输入6位验证码" maxlength="6"/>
            <el-button type="primary" plain :disabled="codeCountdown > 0" @click="handleSendCode">
              {{ codeCountdown > 0 ? `${codeCountdown}s` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="resetForm.newPassword" type="password" show-password placeholder="设置新密码"/>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="resetForm.confirmPassword" type="password" show-password placeholder="再次输入新密码"/>
        </el-form-item>

        <el-button type="primary" class="full-width" @click="handleReset(resetRef)">重置密码</el-button>

        <div class="auth-footer">
          <el-link type="primary" :underline="false" style="font-size: 14px;" @click="$router.push('/login')">
            返回登录
          </el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import {ref, reactive, onBeforeUnmount} from 'vue'
import {useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {sendCodeApi, resetPasswordApi} from '@/api/user'

const router = useRouter()
const resetRef = ref()
const resetForm = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

const validatePass2 = (rule, value, callback) => {
  if (value !== resetForm.newPassword) {
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
  newPassword: [
    {required: true, message: '请输入新密码', trigger: 'blur'},
    {min: 6, message: '密码长度不能少于 6 位', trigger: 'blur'}
  ],
  confirmPassword: [
    {required: true, message: '请再次输入密码', trigger: 'blur'},
    {validator: validatePass2, trigger: 'blur'}
  ]
}

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
  if (!resetForm.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  try {
    const res = await sendCodeApi({email: resetForm.email, action: 'reset'})
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

const handleReset = async (formEl) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid) {
      try {
        const res = await resetPasswordApi({
          email: resetForm.email,
          code: resetForm.code,
          new_password: resetForm.newPassword
        })
        if (res.code === 100) {
          ElMessage.success('密码重置成功，请重新登录')
          await router.push('/login')
        } else {
          ElMessage.error(res.msg || '重置失败')
        }
      } catch (err) {
        console.error('重置密码失败', err)
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
</style>

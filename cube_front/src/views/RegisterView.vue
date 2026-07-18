<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <h2>注册 ICube 账号</h2>
      <el-form :model="registerForm" :rules="rules" ref="registerRef" label-position="top">
        <!-- 邮箱 -->
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="请输入常用邮箱"/>
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
          <el-link type="primary" style="font-size: 14px; vertical-align: baseline;" @click="$router.push('/login')">
            去登录
          </el-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import {ref, reactive} from 'vue'
import {ElMessage, ElNotification} from 'element-plus'
import {registerApi} from '@/api/user'
import {useRouter} from "vue-router";

const router = useRouter()
const registerRef = ref()
const registerForm = reactive({
  username: '',   // 新增
  email: '',
  password: '',
  confirmPassword: '',
  bio: ''         // 新增
})

// 自定义校验逻辑：检查两次密码是否一致
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
  password: [
    {required: true, message: '请输入密码', trigger: 'blur'},
    {min: 6, message: '密码长度不能少于 6 位', trigger: 'blur'}
  ],
  confirmPassword: [
    {required: true, message: '请再次输入密码', trigger: 'blur'},
    {validator: validatePass2, trigger: 'blur'}
  ]
}

const handleRegister = async (formEl) => {
  if (!formEl) return
  await formEl.validate(async (valid) => {
    if (valid) {
      try {
        // 1. 自动处理 username：取邮箱 @ 符号前面的部分
        const emailPrefix = registerForm.email.split('@')[0].replace(/[^a-zA-Z0-9]/g, '')
        // 2. 构造符合后端要求的嵌套格式
        const postData = {
          user: {
            username: emailPrefix, // 自动填充处理后的用户名
            email: registerForm.email,
            password: registerForm.password,
            bio: registerForm.bio || "魔方爱好者" // 给个默认值
          }
        }
        // 注意：后端可能不需要 confirmPassword，根据实际情况过滤数据
        // 发送请求
        const res = await registerApi(postData)
        console.log('【正常响应】response.data:', res.data)

        // 判断业务逻辑 code
        if (res.code === 100) {
          ElMessage.success('注册成功，请登录')
          await router.push('/login')
        } else {
          // 处理类似 998 的业务错误码
          // 这里的 res.msg 就是 "email: 具有 Email Address 的 用户 已存在。"
          // 业务逻辑错误（如 email 已存在）
          ElMessage({
                type: 'error',
                message: !res.msg ? '请求服务器异常,请联系管理员' : res.msg
            })
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
  height: 80vh; /* 居中显示 */
}

.auth-card {
  width: 400px;
  padding: 20px;
}

.full-width {
  width: 100%;
  margin-top: 20px;
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